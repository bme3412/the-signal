import SwiftUI

// MARK: - Chapter Role

enum ChapterRole: String, Codable {
    case intro, core, optional, closer

    var displayName: String {
        switch self {
        case .intro: "Intro"
        case .core: "Core"
        case .optional: "Bonus"
        case .closer: "Closer"
        }
    }

    var icon: String {
        switch self {
        case .intro: "sunrise.fill"
        case .core: "circle.fill"
        case .optional: "sparkles"
        case .closer: "flag.checkered"
        }
    }

    var color: Color {
        switch self {
        case .intro: .accentBlue
        case .core: .textPrimary
        case .optional: .accentPurple
        case .closer: .green
        }
    }
}

// MARK: - Script Chapter

/// Chapter as stored inside an episode's script (references segments by
/// index, unlike ManifestChapter which embeds them).
struct ScriptChapter: Codable, Identifiable {
    let title: String
    let role: ChapterRole
    let segmentIndices: [Int]
    let audioURL: String?
    let durationSeconds: Double
    let startSeconds: Double

    var id: String { "\(segmentIndices.first ?? -1)-\(title)" }

    enum CodingKeys: String, CodingKey {
        case title, role
        case segmentIndices = "segment_indices"
        case audioURL = "audio_url"
        case durationSeconds = "duration_seconds"
        case startSeconds = "start_seconds"
    }
}

// MARK: - Manifest

struct ManifestChapter: Codable, Identifiable {
    let index: Int
    let title: String
    let role: ChapterRole
    let audioURL: String?
    let durationSeconds: Double
    let startSeconds: Double
    let segments: [ScriptSegment]

    var id: Int { index }

    enum CodingKeys: String, CodingKey {
        case index, title, role, segments
        case audioURL = "audio_url"
        case durationSeconds = "duration_seconds"
        case startSeconds = "start_seconds"
    }
}

extension ManifestChapter: PlannableChapter {}

struct EpisodeManifest: Codable {
    let episodeId: String
    let status: EpisodeStatus
    let totalDurationSeconds: Double
    let chapters: [ManifestChapter]

    enum CodingKeys: String, CodingKey {
        case episodeId = "episode_id"
        case status
        case totalDurationSeconds = "total_duration_seconds"
        case chapters
    }
}
