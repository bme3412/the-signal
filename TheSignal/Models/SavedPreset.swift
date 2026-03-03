import Foundation
import SwiftData

@Model
final class SavedPreset {
    @Attribute(.unique) var id: UUID
    var name: String
    var icon: String
    var colorHex: String
    var configJSON: Data
    var lastUsedAt: Date?
    var createdAt: Date
    var usageCount: Int

    init(
        name: String,
        icon: String = "star.fill",
        colorHex: String = "#007AFF",
        config: StyleConfig
    ) {
        self.id = UUID()
        self.name = name
        self.icon = icon
        self.colorHex = colorHex
        self.configJSON = (try? JSONEncoder().encode(config)) ?? Data()
        self.lastUsedAt = nil
        self.createdAt = .now
        self.usageCount = 0
    }

    var config: StyleConfig {
        get {
            (try? JSONDecoder().decode(StyleConfig.self, from: configJSON)) ?? StyleConfig()
        }
        set {
            configJSON = (try? JSONEncoder().encode(newValue)) ?? Data()
        }
    }

    func recordUsage() {
        lastUsedAt = .now
        usageCount += 1
    }
}
