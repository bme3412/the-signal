import SwiftUI
import SwiftData

@main
struct TheSignalApp: App {
    @State private var audioManager = AudioManager()
    @State private var selectedEpisodeForPlayer: Episode?

    var body: some Scene {
        WindowGroup {
            ContentView(selectedEpisodeForPlayer: $selectedEpisodeForPlayer)
                .environment(audioManager)
                .preferredColorScheme(.dark)
        }
        .modelContainer(for: [Article.self, SavedPreset.self])
    }
}

struct ContentView: View {
    @Environment(\.modelContext) private var modelContext
    @Environment(AudioManager.self) private var audio
    @Binding var selectedEpisodeForPlayer: Episode?
    @State private var articleStore: ArticleStore?
    @State private var selectedTab = 0

    var body: some View {
        ZStack(alignment: .bottom) {
            if let articleStore {
                TabView(selection: $selectedTab) {
                    Tab("Queue", systemImage: "tray.full.fill", value: 0) {
                        ArticleQueueView()
                    }

                    Tab("Generate", systemImage: "wand.and.stars", value: 1) {
                        GenerateView()
                    }

                    Tab("Episodes", systemImage: "headphones", value: 2) {
                        EpisodeListView()
                    }
                }
                .environment(articleStore)
                .safeAreaInset(edge: .bottom) {
                    MiniPlayer {
                        if let ep = audio.currentEpisode {
                            selectedEpisodeForPlayer = ep
                        }
                    }
                }
            } else {
                ProgressView("Loading…")
                    .frame(maxWidth: .infinity, maxHeight: .infinity)
                    .background(Color.background)
            }
        }
        .fullScreenCover(item: $selectedEpisodeForPlayer) { episode in
            PlayerView(episode: episode)
                .environment(audio)
        }
        .onAppear {
            if articleStore == nil {
                let store = ArticleStore(modelContext: modelContext)
                articleStore = store
                Task { await store.processSharedURLs() }
            }
        }
    }
}
