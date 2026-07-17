import Foundation

// MARK: - Voice Info

struct VoiceInfo: Codable, Identifiable, Hashable {
    let id: String
    let name: String
}

// MARK: - Voice Settings

struct VoiceSettings: Codable, Equatable {
    var stability: Double = 0.4
    var similarityBoost: Double = 0.75
    var style: Double = 0.5
    var speed: Double = 1.0
    var useSpeakerBoost: Bool = true

    enum CodingKeys: String, CodingKey {
        case stability
        case similarityBoost = "similarity_boost"
        case style
        case speed
        case useSpeakerBoost = "use_speaker_boost"
    }
}

// MARK: - Speaker Config

struct SpeakerConfig: Codable, Equatable {
    var voiceId: String
    var settings: VoiceSettings = VoiceSettings()

    enum CodingKeys: String, CodingKey {
        case voiceId = "voice_id"
        case settings
    }
}

// MARK: - Audio Production Config

struct AudioProductionConfig: Codable, Equatable {
    var silenceDurationMs: Int = 300
    var fadeInMs: Int = 0
    var fadeOutMs: Int = 0
    var normalize: Bool = false
    var targetDbfs: Double = -16.0
    var introMusic: Bool = false

    enum CodingKeys: String, CodingKey {
        case silenceDurationMs = "silence_duration_ms"
        case fadeInMs = "fade_in_ms"
        case fadeOutMs = "fade_out_ms"
        case normalize
        case targetDbfs = "target_dbfs"
        case introMusic = "intro_music"
    }
}

// MARK: - Voices Response

struct VoicesResponse: Codable {
    let voices: [VoiceInfo]
    let defaults: [String: [String: String]]
    let settingsRanges: SettingsRanges

    enum CodingKeys: String, CodingKey {
        case voices, defaults
        case settingsRanges = "settings_ranges"
    }
}

struct SettingsRanges: Codable {
    let stability: SettingRange
    let similarityBoost: SettingRange
    let style: SettingRange

    enum CodingKeys: String, CodingKey {
        case stability
        case similarityBoost = "similarity_boost"
        case style
    }
}

struct SettingRange: Codable {
    let min: Double
    let max: Double
    let `default`: Double
}
