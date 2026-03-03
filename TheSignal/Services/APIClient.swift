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

actor APIClient {
    static let shared = APIClient()

    #if DEBUG
    private var baseURL = "http://localhost:8000"
    #else
    private var baseURL = "http://localhost:8000"
    #endif

    private let session: URLSession
    private let decoder: JSONDecoder
    private let encoder: JSONEncoder
    private let maxRetries = 3

    private init() {
        let config = URLSessionConfiguration.default
        config.timeoutIntervalForRequest = 30
        config.timeoutIntervalForResource = 300
        session = URLSession(configuration: config)

        decoder = JSONDecoder()
        decoder.dateDecodingStrategy = .iso8601

        encoder = JSONEncoder()
        encoder.dateEncodingStrategy = .iso8601
    }

    func setBaseURL(_ url: String) {
        baseURL = url
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

    func downloadAudio(episodeId: String) async throws -> URL {
        let url = URL(string: "\(baseURL)/api/episodes/\(episodeId)/audio")!
        let (tempURL, response) = try await session.download(from: url)

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
