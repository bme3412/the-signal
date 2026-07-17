import SwiftUI

/// Full transcript of an episode, grouped by chapter when chapter data is
/// available. Presented from the player and from the episode list.
struct TranscriptView: View {
    let script: EpisodeScript
    let title: String
    @Environment(\.dismiss) private var dismiss

    var body: some View {
        NavigationStack {
            ScrollView {
                LazyVStack(alignment: .leading, spacing: 12) {
                    if let chapters = script.chapters, !chapters.isEmpty {
                        ForEach(chapters) { chapter in
                            chapterHeader(chapter)
                                .padding(.top, 8)
                            ForEach(
                                chapter.segmentIndices.filter { script.segments.indices.contains($0) },
                                id: \.self
                            ) { index in
                                segmentView(script.segments[index])
                            }
                        }
                    } else {
                        ForEach(script.segments) { segment in
                            segmentView(segment)
                        }
                    }
                }
                .padding()
            }
            .background(Color.background)
            .navigationTitle(title)
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .topBarTrailing) {
                    Button("Done") { dismiss() }
                }
            }
        }
    }

    private func chapterHeader(_ chapter: ScriptChapter) -> some View {
        HStack(spacing: 8) {
            Image(systemName: chapter.role.icon)
                .font(.caption)
                .foregroundStyle(chapter.role.color)
            Text(chapter.title)
                .font(.subheadline.weight(.bold))
                .foregroundStyle(Color.textPrimary)
            if chapter.role == .optional {
                Text("BONUS")
                    .font(.system(size: 9, weight: .bold, design: .monospaced))
                    .padding(.horizontal, 5)
                    .padding(.vertical, 2)
                    .background(Color.accentPurple.opacity(0.2), in: .capsule)
                    .foregroundStyle(Color.accentPurple)
            }
            Spacer()
            if chapter.durationSeconds > 0 {
                Text(formatDuration(chapter.durationSeconds))
                    .font(.caption2.monospaced())
                    .foregroundStyle(Color.textMuted)
            }
        }
        .padding(.vertical, 6)
        .padding(.horizontal, 10)
        .background(Color.surface, in: .rect(cornerRadius: 8))
    }

    private func segmentView(_ segment: ScriptSegment) -> some View {
        VStack(alignment: .leading, spacing: 2) {
            Text(segment.speaker)
                .font(.caption.weight(.bold).monospaced())
                .foregroundStyle(segment.speakerColor)
            Text(segment.text)
                .font(.body)
                .foregroundStyle(Color.textPrimary)
        }
    }

    private func formatDuration(_ seconds: Double) -> String {
        let mins = Int(seconds) / 60
        let secs = Int(seconds) % 60
        return String(format: "%d:%02d", mins, secs)
    }
}
