import Foundation
import SwiftData

@Model
final class Article {
    @Attribute(.unique) var id: UUID
    var title: String
    var source: String
    var url: URL?
    var text: String
    var summary: String?
    var wordCount: Int
    var createdAt: Date
    var isSelected: Bool

    init(
        id: UUID = UUID(),
        title: String,
        source: String,
        url: URL? = nil,
        text: String,
        summary: String? = nil,
        wordCount: Int = 0,
        createdAt: Date = .now,
        isSelected: Bool = true
    ) {
        self.id = id
        self.title = title
        self.source = source
        self.url = url
        self.text = text
        self.summary = summary
        self.wordCount = wordCount > 0 ? wordCount : text.split(separator: " ").count
        self.createdAt = createdAt
        self.isSelected = isSelected
    }
}

// MARK: - API DTO (matches backend JSON)

struct ArticleDTO: Codable, Identifiable {
    let id: String
    let title: String
    let source: String
    let url: String?
    let text: String
    let summary: String?
    let wordCount: Int
    let createdAt: Date

    enum CodingKeys: String, CodingKey {
        case id, title, source, url, text, summary
        case wordCount = "word_count"
        case createdAt = "created_at"
    }
}

struct ArticleCreateDTO: Codable {
    var url: String?
    var title: String?
    var text: String?
    var source: String?
}
