import SwiftUI
import SwiftData

struct ArticleQueueView: View {
    @Environment(ArticleStore.self) private var store
    @State private var showingAddSheet = false
    @State private var articles: [Article] = []

    var body: some View {
        NavigationStack {
            Group {
                if articles.isEmpty {
                    emptyState
                } else {
                    articleList
                }
            }
            .navigationTitle("Queue")
            .toolbar {
                ToolbarItem(placement: .topBarTrailing) {
                    Button { showingAddSheet = true } label: {
                        Image(systemName: "plus.circle.fill")
                            .font(.title3)
                    }
                }
            }
            .sheet(isPresented: $showingAddSheet) {
                AddArticleSheet()
            }
            .onAppear { refreshArticles() }
        }
    }

    private var articleList: some View {
        List {
            Section {
                ForEach(articles, id: \.id) { article in
                    ArticleRow(article: article) {
                        store.toggleSelection(article)
                        refreshArticles()
                    }
                    .swipeActions(edge: .trailing, allowsFullSwipe: true) {
                        Button(role: .destructive) {
                            store.deleteArticle(article)
                            refreshArticles()
                        } label: {
                            Label("Delete", systemImage: "trash")
                        }
                    }
                }
            } header: {
                let selected = articles.filter(\.isSelected).count
                Text("\(selected) of \(articles.count) selected")
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }
        }
        .listStyle(.plain)
    }

    private var emptyState: some View {
        ContentUnavailableView {
            Label("No Articles Yet", systemImage: "tray")
        } description: {
            Text("Share articles from Safari, Twitter, or any app.\nOr tap + to paste a URL or text.")
        } actions: {
            Button("Add Manually") { showingAddSheet = true }
                .buttonStyle(.borderedProminent)
        }
    }

    private func refreshArticles() {
        articles = store.todaysArticles()
    }
}
