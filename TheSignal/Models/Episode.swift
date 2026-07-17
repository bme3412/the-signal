import SwiftUI

// MARK: - Episode Status

enum EpisodeStatus: String, Codable {
    case queued, summarizing, scripting, synthesizing, mixing, ready, failed

    var displayName: String {
        switch self {
        case .queued: "Queued"
        case .summarizing: "Summarizing"
        case .scripting: "Writing Script"
        case .synthesizing: "Generating Audio"
        case .mixing: "Mixing"
        case .ready: "Ready"
        case .failed: "Failed"
        }
    }

    var icon: String {
        switch self {
        case .queued: "clock.fill"
        case .summarizing: "doc.text.magnifyingglass"
        case .scripting: "pencil.line"
        case .synthesizing: "waveform"
        case .mixing: "slider.horizontal.3"
        case .ready: "checkmark.circle.fill"
        case .failed: "xmark.octagon.fill"
        }
    }

    var color: Color {
        switch self {
        case .queued: .gray
        case .summarizing, .scripting: .blue
        case .synthesizing, .mixing: .purple
        case .ready: .green
        case .failed: .red
        }
    }

    var isTerminal: Bool {
        self == .ready || self == .failed
    }

    var stepIndex: Int {
        switch self {
        case .queued: 0
        case .summarizing: 1
        case .scripting: 2
        case .synthesizing: 3
        case .mixing: 4
        case .ready: 5
        case .failed: -1
        }
    }
}

// MARK: - Script

struct ScriptSegment: Codable, Identifiable {
    let speaker: String
    let text: String
    let charCount: Int
    let durationSeconds: Double?

    var id: String { "\(speaker)-\(charCount)-\(text.prefix(20))" }

    enum CodingKeys: String, CodingKey {
        case speaker, text
        case charCount = "char_count"
        case durationSeconds = "duration_seconds"
    }

    var speakerColor: Color {
        switch speaker {
        case "ALEX": .blue
        case "JAMIE": .orange
        case "HOST": .blue
        case "BULL": .green
        case "BEAR": .red
        default: .gray
        }
    }
}

struct EpisodeScript: Codable {
    let rawText: String
    let segments: [ScriptSegment]
    let chapters: [ScriptChapter]?
    let wordCount: Int
    let estimatedMinutes: Double

    enum CodingKeys: String, CodingKey {
        case rawText = "raw_text"
        case segments, chapters
        case wordCount = "word_count"
        case estimatedMinutes = "estimated_minutes"
    }
}

// MARK: - Pipeline Metrics

struct PipelineMetrics: Codable {
    let summarizeTimeMs: Double
    let scriptTimeMs: Double
    let ttsTimeMs: Double
    let mixTimeMs: Double
    let totalTimeMs: Double
    let scriptTokensIn: Int
    let scriptTokensOut: Int
    let ttsCharacters: Int
    let estimatedCostUsd: Double

    enum CodingKeys: String, CodingKey {
        case summarizeTimeMs = "summarize_time_ms"
        case scriptTimeMs = "script_time_ms"
        case ttsTimeMs = "tts_time_ms"
        case mixTimeMs = "mix_time_ms"
        case totalTimeMs = "total_time_ms"
        case scriptTokensIn = "script_tokens_in"
        case scriptTokensOut = "script_tokens_out"
        case ttsCharacters = "tts_characters"
        case estimatedCostUsd = "estimated_cost_usd"
    }
}

// MARK: - Episode

struct Episode: Codable, Identifiable {
    let id: String
    let title: String?
    let status: EpisodeStatus
    let style: StyleConfig
    let articleIds: [String]
    let script: EpisodeScript?
    let audioURL: String?
    let audioDuration: Double?
    let metrics: PipelineMetrics?
    let error: String?
    let createdAt: Date
    let completedAt: Date?

    var displayTitle: String {
        title ?? "Episode \(id.prefix(8))"
    }

    enum CodingKeys: String, CodingKey {
        case id, title, status, style, script, error
        case articleIds = "article_ids"
        case audioURL = "audio_url"
        case audioDuration = "audio_duration_seconds"
        case metrics
        case createdAt = "created_at"
        case completedAt = "completed_at"
    }
}

// MARK: - Episode Request

struct EpisodeRequest: Codable {
    let articleIds: [String]
    let style: StyleConfig
    var voiceMapping: [String: String]?
    var voiceConfig: [String: SpeakerConfig]?
    var audioConfig: AudioProductionConfig = AudioProductionConfig()
    var targetMinutes: Int = 20

    enum CodingKeys: String, CodingKey {
        case articleIds = "article_ids"
        case style
        case voiceMapping = "voice_mapping"
        case voiceConfig = "voice_config"
        case audioConfig = "audio_config"
        case targetMinutes = "target_minutes"
    }
}
