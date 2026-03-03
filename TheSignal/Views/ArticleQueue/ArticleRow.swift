import SwiftUI

struct ArticleRow: View {
    let article: Article
    let onToggle: () -> Void

    @State private var showingPreview = false

    var body: some View {
        Button(action: onToggle) {
            HStack(spacing: 12) {
                Image(systemName: article.isSelected ? "checkmark.circle.fill" : "circle")
                    .font(.title3)
                    .foregroundStyle(article.isSelected ? Color.accentBlue : .secondary)

                VStack(alignment: .leading, spacing: 4) {
                    Text(article.title)
                        .font(.subheadline.weight(.medium))
                        .foregroundStyle(Color.textPrimary)
                        .lineLimit(2)

                    HStack(spacing: 8) {
                        Text(article.source)
                            .font(.caption.monospaced())
                            .foregroundStyle(Color.textSecondary)

                        Text("·")
                            .foregroundStyle(Color.textMuted)

                        Text("\(article.wordCount) words")
                            .font(.caption.monospaced())
                            .foregroundStyle(Color.textMuted)

                        Spacer()

                        Text(article.createdAt, style: .time)
                            .font(.caption2.monospaced())
                            .foregroundStyle(Color.textMuted)
                    }
                }
            }
            .padding(.vertical, 4)
        }
        .buttonStyle(.plain)
        .contextMenu {
            Button {
                showingPreview = true
            } label: {
                Label("Preview", systemImage: "doc.text")
            }
            if let url = article.url {
                ShareLink(item: url) {
                    Label("Share", systemImage: "square.and.arrow.up")
                }
            }
        }
        .sheet(isPresented: $showingPreview) {
            NavigationStack {
                ScrollView {
                    Text(article.text)
                        .font(.body)
                        .padding()
                }
                .navigationTitle(article.title)
                .navigationBarTitleDisplayMode(.inline)
                .toolbar {
                    ToolbarItem(placement: .topBarTrailing) {
                        Button("Done") { showingPreview = false }
                    }
                }
            }
        }
    }
}
