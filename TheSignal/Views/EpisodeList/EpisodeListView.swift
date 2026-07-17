import SwiftUI

struct EpisodeListView: View {
    @Environment(AudioManager.self) private var audio
    @State private var episodes: [Episode] = []
    @State private var isLoading = false
    @State private var selectedEpisode: Episode?
    @State private var transcriptEpisode: Episode?

    var body: some View {
        NavigationStack {
            Group {
                if episodes.isEmpty && !isLoading {
                    ContentUnavailableView {
                        Label("No Episodes", systemImage: "headphones")
                    } description: {
                        Text("Generate your first episode from the Queue tab.")
                    }
                } else {
                    List(episodes) { episode in
                        EpisodeRow(episode: episode) {
                            selectedEpisode = episode
                        } onPlay: {
                            Task { await audio.play(episode: episode) }
                        }
                        .contextMenu {
                            if episode.script != nil {
                                Button {
                                    transcriptEpisode = episode
                                } label: {
                                    Label("View Transcript", systemImage: "doc.text")
                                }
                            }
                        }
                        .swipeActions(edge: .leading) {
                            if episode.script != nil {
                                Button {
                                    transcriptEpisode = episode
                                } label: {
                                    Label("Transcript", systemImage: "doc.text")
                                }
                                .tint(Color.accentBlue)
                            }
                        }
                    }
                    .listStyle(.plain)
                }
            }
            .navigationTitle("Episodes")
            .refreshable { await loadEpisodes() }
            .task { await loadEpisodes() }
            .fullScreenCover(item: $selectedEpisode) { ep in
                PlayerView(episode: ep)
            }
            .sheet(item: $transcriptEpisode) { ep in
                if let script = ep.script {
                    TranscriptView(script: script, title: ep.displayTitle)
                }
            }
            .overlay {
                if isLoading && episodes.isEmpty {
                    ProgressView()
                }
            }
        }
    }

    private func loadEpisodes() async {
        isLoading = true
        defer { isLoading = false }
        do {
            episodes = try await APIClient.shared.listEpisodes()
        } catch {
            print("Failed to load episodes: \(error)")
        }
    }
}
