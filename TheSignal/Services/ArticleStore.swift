import Foundation
import SwiftData

@Observable
final class ArticleStore {
    private let modelContext: ModelContext

    init(modelContext: ModelContext) {
        self.modelContext = modelContext
    }

    func addArticle(title: String, source: String, url: URL? = nil, text: String) {
        let article = Article(title: title, source: source, url: url, text: text)
        modelContext.insert(article)
        try? modelContext.save()
    }

    func addFromDTO(_ dto: ArticleDTO) {
        let article = Article(
            title: dto.title,
            source: dto.source,
            url: dto.url.flatMap { URL(string: $0) },
            text: dto.text,
            summary: dto.summary,
            wordCount: dto.wordCount,
            createdAt: dto.createdAt
        )
        modelContext.insert(article)
        try? modelContext.save()
    }

    func todaysArticles() -> [Article] {
        let calendar = Calendar.current
        let startOfDay = calendar.startOfDay(for: .now)
        let predicate = #Predicate<Article> { article in
            article.createdAt >= startOfDay
        }
        let descriptor = FetchDescriptor(predicate: predicate, sortBy: [SortDescriptor(\.createdAt, order: .reverse)])
        return (try? modelContext.fetch(descriptor)) ?? []
    }

    func selectedArticles() -> [Article] {
        let calendar = Calendar.current
        let startOfDay = calendar.startOfDay(for: .now)
        let predicate = #Predicate<Article> { article in
            article.createdAt >= startOfDay && article.isSelected
        }
        let descriptor = FetchDescriptor(predicate: predicate, sortBy: [SortDescriptor(\.createdAt, order: .reverse)])
        return (try? modelContext.fetch(descriptor)) ?? []
    }

    func allArticles() -> [Article] {
        let descriptor = FetchDescriptor<Article>(sortBy: [SortDescriptor(\.createdAt, order: .reverse)])
        return (try? modelContext.fetch(descriptor)) ?? []
    }

    func toggleSelection(_ article: Article) {
        article.isSelected.toggle()
        try? modelContext.save()
    }

    func deleteArticle(_ article: Article) {
        modelContext.delete(article)
        try? modelContext.save()
    }

    // MARK: - Share Extension Ingestion

    func processSharedURLs() async {
        let defaults = UserDefaults(suiteName: "group.com.thesignal.shared")
        guard let urls = defaults?.stringArray(forKey: "pendingURLs"), !urls.isEmpty else { return }

        for urlString in urls {
            guard let url = URL(string: urlString) else { continue }
            do {
                let dto = try await APIClient.shared.submitArticle(url: url)
                addFromDTO(dto)
            } catch {
                addArticle(title: url.host ?? "Shared Link", source: "share", url: url, text: urlString)
            }
        }

        defaults?.removeObject(forKey: "pendingURLs")
    }
}
