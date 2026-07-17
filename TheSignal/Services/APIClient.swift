import Foundation

enum APIError: LocalizedError {
    case invalidURL
    case badStatus(Int, String)
    case decodingFailed(Error)
    case networkError(Error)

    var errorDescription: String? {
        switch self {
        case .invalidURL: "Invalid URL"
        case .badStatus(let code, let body): "HTTP \(code): \(body)"
        case .decodingFailed(let err): "Decoding failed: \(err.localizedDescription)"
        case .networkError(let err): "Network error: \(err.localizedDescription)"
        }
    }
}

struct HealthResponse: Codable {
    let status: String
    let anthropicConfigured: Bool
    let elevenlabsConfigured: Bool

    enum CodingKeys: String, CodingKey {
        case status
        case anthropicConfigured = "anthropic_configured"
        case elevenlabsConfigured = "elevenlabs_configured"
    }
}

actor APIClient {
    static let shared = APIClient()

    static let defaultBaseURL = "http://localhost:8000"
    static let baseURLDefaultsKey = "backendBaseURL"
    static let apiTokenDefaultsKey = "backendAPIToken"

    private var baseURL: String
    private var apiToken: String

    private let session: URLSession
    private let decoder: JSONDecoder
    private let encoder: JSONEncoder
    private let maxRetries = 3

    private init() {
        baseURL = UserDefaults.standard.string(forKey: Self.baseURLDefaultsKey)
            ?? Self.defaultBaseURL
        apiToken = UserDefaults.standard.string(forKey: Self.apiTokenDefaultsKey) ?? ""
        let config = URLSessionConfiguration.default
        config.timeoutIntervalForRequest = 30
        config.timeoutIntervalForResource = 300
        session = URLSession(configuration: config)

        decoder = JSONDecoder()
        // The backend (pydantic) emits fractional seconds, which the plain
        // .iso8601 strategy cannot parse.
        let isoFractional = ISO8601DateFormatter()
        isoFractional.formatOptions = [.withInternetDateTime, .withFractionalSeconds]
        let iso = ISO8601DateFormatter()
        decoder.dateDecodingStrategy = .custom { decoder in
            let container = try decoder.singleValueContainer()
            let raw = try container.decode(String.self)
            if let date = isoFractional.date(from: raw) ?? iso.date(from: raw) {
                return date
            }
            throw DecodingError.dataCorruptedError(
                in: container, debugDescription: "Unparseable date: \(raw)"
            )
        }

        encoder = JSONEncoder()
        encoder.dateEncodingStrategy = .iso8601
    }

    func setBaseURL(_ url: String) {
        baseURL = url
        UserDefaults.standard.set(url, forKey: Self.baseURLDefaultsKey)
    }

    func setAPIToken(_ token: String) {
        apiToken = token.trimmingCharacters(in: .whitespacesAndNewlines)
        UserDefaults.standard.set(apiToken, forKey: Self.apiTokenDefaultsKey)
    }

    private func authorize(_ request: inout URLRequest) {
        if !apiToken.isEmpty {
            request.setValue("Bearer \(apiToken)", forHTTPHeaderField: "Authorization")
        }
    }

    func checkHealth() async throws -> HealthResponse {
        try await get("/health")
    }

    // MARK: - Articles

    func submitArticle(url: URL) async throws -> ArticleDTO {
        let body = ArticleCreateDTO(url: url.absoluteString)
        return try await post("/api/articles", body: body)
    }

    func submitArticle(title: String, text: String, source: String = "manual") async throws -> ArticleDTO {
        let body = ArticleCreateDTO(title: title, text: text, source: source)
        return try await post("/api/articles", body: body)
    }

    func listArticles() async throws -> [ArticleDTO] {
        try await get("/api/articles")
    }

    func deleteArticle(id: String) async throws {
        let _: [String: Bool] = try await delete("/api/articles/\(id)")
    }

    // MARK: - Episodes

    func getVoices() async throws -> VoicesResponse {
        try await get("/api/episodes/voices")
    }

    func generateEpisode(request: EpisodeRequest) async throws -> Episode {
        try await post("/api/episodes/generate", body: request)
    }

    func getEpisode(id: String) async throws -> Episode {
        try await get("/api/episodes/\(id)")
    }

    func getScript(episodeId: String) async throws -> EpisodeScript {
        try await get("/api/episodes/\(episodeId)/script")
    }

    func listEpisodes() async throws -> [Episode] {
        try await get("/api/episodes")
    }

    func getManifest(episodeId: String) async throws -> EpisodeManifest {
        try await get("/api/episodes/\(episodeId)/manifest")
    }

    func downloadChapterAudio(episodeId: String, chapter: ManifestChapter) async throws -> URL {
        guard let path = chapter.audioURL, let url = URL(string: "\(baseURL)\(path)") else {
            throw APIError.invalidURL
        }
        var dreq = URLRequest(url: url)
        authorize(&dreq)
        let (tempURL, response) = try await session.download(for: dreq)

        guard let http = response as? HTTPURLResponse, http.statusCode == 200 else {
            throw APIError.badStatus(
                (response as? HTTPURLResponse)?.statusCode ?? 0,
                "Chapter download failed"
            )
        }

        let docs = FileManager.default.urls(for: .documentDirectory, in: .userDomainMask)[0]
        let name = String(format: "%02d.mp3", chapter.index)
        let dest = docs.appendingPathComponent("episodes/\(episodeId)/chapters/\(name)")
        try FileManager.default.createDirectory(
            at: dest.deletingLastPathComponent(),
            withIntermediateDirectories: true
        )
        if FileManager.default.fileExists(atPath: dest.path) {
            try FileManager.default.removeItem(at: dest)
        }
        try FileManager.default.moveItem(at: tempURL, to: dest)
        return dest
    }

    func downloadAudio(episodeId: String) async throws -> URL {
        let url = URL(string: "\(baseURL)/api/episodes/\(episodeId)/audio")!
        var dreq = URLRequest(url: url)
        authorize(&dreq)
        let (tempURL, response) = try await session.download(for: dreq)

        guard let http = response as? HTTPURLResponse, http.statusCode == 200 else {
            throw APIError.badStatus(
                (response as? HTTPURLResponse)?.statusCode ?? 0,
                "Audio download failed"
            )
        }

        let docs = FileManager.default.urls(for: .documentDirectory, in: .userDomainMask)[0]
        let dest = docs.appendingPathComponent("episodes/\(episodeId).mp3")
        try FileManager.default.createDirectory(
            at: dest.deletingLastPathComponent(),
            withIntermediateDirectories: true
        )
        if FileManager.default.fileExists(atPath: dest.path) {
            try FileManager.default.removeItem(at: dest)
        }
        try FileManager.default.moveItem(at: tempURL, to: dest)
        return dest
    }

    // MARK: - Generic HTTP

    private func get<T: Decodable>(_ path: String) async throws -> T {
        try await request(path, method: "GET", body: nil as String?)
    }

    private func post<B: Encodable, T: Decodable>(_ path: String, body: B) async throws -> T {
        try await request(path, method: "POST", body: body)
    }

    private func delete<T: Decodable>(_ path: String) async throws -> T {
        try await request(path, method: "DELETE", body: nil as String?)
    }

    private func request<B: Encodable, T: Decodable>(
        _ path: String,
        method: String,
        body: B?
    ) async throws -> T {
        guard let url = URL(string: "\(baseURL)\(path)") else {
            throw APIError.invalidURL
        }

        var req = URLRequest(url: url)
        req.httpMethod = method
        req.setValue("application/json", forHTTPHeaderField: "Content-Type")
        authorize(&req)

        if let body {
            req.httpBody = try encoder.encode(body)
        }

        var lastError: Error = APIError.networkError(
            NSError(domain: "", code: 0, userInfo: [NSLocalizedDescriptionKey: "No attempts made"])
        )

        for attempt in 0..<maxRetries {
            do {
                let (data, response) = try await session.data(for: req)
                guard let http = response as? HTTPURLResponse else {
                    throw APIError.networkError(
                        NSError(domain: "", code: 0, userInfo: [NSLocalizedDescriptionKey: "Not HTTP"])
                    )
                }

                guard (200...299).contains(http.statusCode) else {
                    let body = String(data: data, encoding: .utf8) ?? ""
                    if http.statusCode >= 500, attempt < maxRetries - 1 {
                        let delay = UInt64(pow(2.0, Double(attempt))) * 1_000_000_000
                        try await Task.sleep(nanoseconds: delay)
                        lastError = APIError.badStatus(http.statusCode, body)
                        continue
                    }
                    throw APIError.badStatus(http.statusCode, body)
                }

                do {
                    return try decoder.decode(T.self, from: data)
                } catch {
                    throw APIError.decodingFailed(error)
                }
            } catch let error as APIError {
                throw error
            } catch {
                if attempt < maxRetries - 1 {
                    let delay = UInt64(pow(2.0, Double(attempt))) * 1_000_000_000
                    try await Task.sleep(nanoseconds: delay)
                    lastError = error
                    continue
                }
                throw APIError.networkError(error)
            }
        }

        throw lastError
    }
}
