import MapKit
import SwiftUI

/// Pick a time budget — by hand or from the walking ETA to a destination —
/// and preview which chapters will play before starting an adaptive walk.
struct WalkPlanSheet: View {
    enum WalkMode: String, CaseIterable {
        case timer = "Timer"
        case destination = "Destination"
    }

    let episode: Episode
    @Environment(AudioManager.self) private var audio
    @Environment(\.dismiss) private var dismiss

    @State private var manifest: EpisodeManifest?
    @State private var loadError: String?
    @State private var budgetMinutes = 20
    @State private var starting = false

    @State private var mode: WalkMode = .timer
    @State private var tracker = RouteTracker()
    @State private var searchQuery = ""
    @State private var searchResults: [MKMapItem] = []
    @State private var selectedDestination: MKMapItem?
    @State private var routeETA: TimeInterval?
    @State private var searching = false

    private static let presets = [10, 15, 20, 30, 45]

    private var budgetSeconds: TimeInterval? {
        switch mode {
        case .timer: Double(budgetMinutes) * 60
        case .destination: routeETA
        }
    }

    private var plan: AdaptivePlan? {
        guard let manifest, let budgetSeconds else { return nil }
        return AdaptivePlanner.plan(chapters: manifest.chapters, budgetSeconds: budgetSeconds)
    }

    var body: some View {
        NavigationStack {
            Group {
                if let manifest {
                    content(manifest: manifest)
                } else if let loadError {
                    ContentUnavailableView(
                        "No Chapter Data",
                        systemImage: "map",
                        description: Text(loadError)
                    )
                } else {
                    ProgressView("Loading chapters…")
                }
            }
            .navigationTitle("Fit to My Walk")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .topBarTrailing) {
                    Button("Cancel") { dismiss() }
                }
            }
            .background(Color.background)
        }
        .task { await loadManifest() }
        .onChange(of: mode) { _, newMode in
            if newMode == .destination {
                tracker.requestAuthorization()
            }
        }
    }

    // MARK: - Content

    private func content(manifest: EpisodeManifest) -> some View {
        VStack(spacing: 0) {
            Picker("Mode", selection: $mode) {
                ForEach(WalkMode.allCases, id: \.self) { m in
                    Text(m.rawValue).tag(m)
                }
            }
            .pickerStyle(.segmented)
            .padding([.horizontal, .top])

            switch mode {
            case .timer:
                budgetPicker
                    .padding()
            case .destination:
                destinationPicker
                    .padding()
            }

            List {
                Section("Chapters") {
                    ForEach(manifest.chapters) { chapter in
                        chapterRow(
                            chapter,
                            plays: plan?.chapterIndices.contains(chapter.index) ?? true
                        )
                    }
                }
            }
            .scrollContentBackground(.hidden)

            if let plan {
                planSummary(plan)
                    .padding([.horizontal, .bottom])
            }

            Button {
                startWalk()
            } label: {
                Label(
                    starting ? "Starting…" : "Start Walk",
                    systemImage: "figure.walk"
                )
                .font(.headline)
                .frame(maxWidth: .infinity)
                .padding(.vertical, 14)
                .background(
                    plan == nil ? Color.surface : Color.accentBlue,
                    in: .rect(cornerRadius: 14)
                )
                .foregroundStyle(plan == nil ? Color.textMuted : .white)
            }
            .disabled(starting || plan == nil)
            .padding([.horizontal, .bottom])
        }
    }

    private func startWalk() {
        starting = true
        Task {
            switch mode {
            case .timer:
                await audio.startWalk(episode: episode, budgetMinutes: budgetMinutes)
            case .destination:
                guard let destination = selectedDestination else { return }
                await audio.startWalk(episode: episode, destination: destination, tracker: tracker)
            }
            dismiss()
        }
    }

    // MARK: - Destination Mode

    @ViewBuilder
    private var destinationPicker: some View {
        VStack(alignment: .leading, spacing: 10) {
            if let destination = selectedDestination {
                HStack(spacing: 10) {
                    Image(systemName: "mappin.circle.fill")
                        .foregroundStyle(Color.accentBlue)
                    VStack(alignment: .leading, spacing: 2) {
                        Text(destination.name ?? "Destination")
                            .font(.subheadline.weight(.medium))
                            .foregroundStyle(Color.textPrimary)
                            .lineLimit(1)
                        if let eta = routeETA {
                            Text("≈ \(Int((eta / 60).rounded())) min walk")
                                .font(.caption.monospaced())
                                .foregroundStyle(Color.textSecondary)
                        } else {
                            Text("Calculating walking time…")
                                .font(.caption)
                                .foregroundStyle(Color.textMuted)
                        }
                    }
                    Spacer()
                    Button("Change") {
                        selectedDestination = nil
                        routeETA = nil
                    }
                    .font(.caption)
                    .foregroundStyle(Color.accentBlue)
                }
                .padding(12)
                .background(Color.surface, in: .rect(cornerRadius: 12))
            } else if tracker.authorizationStatus == .denied || tracker.authorizationStatus == .restricted {
                Label(
                    "Location access is off — enable it in Settings, or use Timer mode.",
                    systemImage: "location.slash"
                )
                .font(.caption)
                .foregroundStyle(Color.orange)
            } else {
                HStack(spacing: 8) {
                    Image(systemName: "magnifyingglass")
                        .foregroundStyle(Color.textMuted)
                    TextField("Where are you walking to?", text: $searchQuery)
                        .textFieldStyle(.plain)
                        .foregroundStyle(Color.textPrimary)
                        .submitLabel(.search)
                        .onSubmit { Task { await search() } }
                    if searching {
                        ProgressView()
                            .controlSize(.small)
                    }
                }
                .padding(10)
                .background(Color.surface, in: .rect(cornerRadius: 10))

                ForEach(Array(searchResults.prefix(5).enumerated()), id: \.offset) { _, item in
                    Button {
                        select(item)
                    } label: {
                        HStack(spacing: 8) {
                            Image(systemName: "mappin")
                                .font(.caption)
                                .foregroundStyle(Color.textMuted)
                            VStack(alignment: .leading, spacing: 1) {
                                Text(item.name ?? "Unknown")
                                    .font(.subheadline)
                                    .foregroundStyle(Color.textPrimary)
                                    .lineLimit(1)
                                if let subtitle = resultSubtitle(item) {
                                    Text(subtitle)
                                        .font(.caption2)
                                        .foregroundStyle(Color.textMuted)
                                        .lineLimit(1)
                                }
                            }
                            Spacer()
                        }
                        .padding(.vertical, 6)
                        .padding(.horizontal, 4)
                    }
                    .buttonStyle(.plain)
                }
            }
        }
    }

    private func resultSubtitle(_ item: MKMapItem) -> String? {
        if let itemLocation = item.placemark.location, let here = tracker.currentLocation {
            let meters = here.distance(from: itemLocation)
            return meters < 1000
                ? "\(Int(meters)) m away"
                : String(format: "%.1f km away", meters / 1000)
        }
        return item.placemark.title
    }

    private func search() async {
        searching = true
        defer { searching = false }
        searchResults = (try? await tracker.searchDestinations(query: searchQuery)) ?? []
    }

    private func select(_ item: MKMapItem) {
        selectedDestination = item
        searchResults = []
        Task {
            routeETA = try? await tracker.walkingETA(to: item)
        }
    }

    private var budgetPicker: some View {
        VStack(spacing: 12) {
            HStack {
                Text("I have")
                    .foregroundStyle(Color.textSecondary)
                Text("\(budgetMinutes) min")
                    .font(.title2.weight(.bold).monospaced())
                    .foregroundStyle(Color.textPrimary)
                    .contentTransition(.numericText())
                Spacer()
                Stepper("", value: $budgetMinutes, in: 5...120, step: 5)
                    .labelsHidden()
            }

            HStack(spacing: 8) {
                ForEach(Self.presets, id: \.self) { mins in
                    Button {
                        withAnimation { budgetMinutes = mins }
                    } label: {
                        Text("\(mins)m")
                            .font(.caption.weight(.medium).monospaced())
                            .padding(.horizontal, 12)
                            .padding(.vertical, 6)
                            .background(
                                budgetMinutes == mins ? Color.accentBlue.opacity(0.2) : Color.surface,
                                in: .capsule
                            )
                            .foregroundStyle(budgetMinutes == mins ? Color.accentBlue : Color.textMuted)
                    }
                    .buttonStyle(.plain)
                }
                Spacer()
            }
        }
    }

    private func chapterRow(_ chapter: ManifestChapter, plays: Bool) -> some View {
        HStack(spacing: 10) {
            Image(systemName: chapter.role.icon)
                .font(.caption)
                .foregroundStyle(chapter.role.color)
                .frame(width: 20)

            VStack(alignment: .leading, spacing: 2) {
                Text(chapter.title)
                    .font(.subheadline)
                    .foregroundStyle(plays ? Color.textPrimary : Color.textMuted)
                    .strikethrough(!plays)
                Text("\(chapter.role.displayName) · \(formatDuration(chapter.durationSeconds))")
                    .font(.caption2.monospaced())
                    .foregroundStyle(Color.textMuted)
            }

            Spacer()

            Image(systemName: plays ? "checkmark.circle.fill" : "minus.circle")
                .foregroundStyle(plays ? Color.green : Color.textMuted)
        }
        .listRowBackground(Color.surface)
    }

    private func planSummary(_ plan: AdaptivePlan) -> some View {
        HStack {
            VStack(alignment: .leading, spacing: 2) {
                Text(summaryLine(plan))
                    .font(.subheadline.weight(.medium))
                    .foregroundStyle(plan.overBudget ? Color.orange : Color.textPrimary)
                if plan.rate != 1.0 {
                    Text(String(format: "Plays at %.2fx to land on time", plan.rate))
                        .font(.caption)
                        .foregroundStyle(Color.textSecondary)
                }
            }
            Spacer()
        }
        .padding(12)
        .background(Color.surface, in: .rect(cornerRadius: 12))
    }

    private func summaryLine(_ plan: AdaptivePlan) -> String {
        let mins = Int((plan.wallClockSeconds / 60).rounded())
        if plan.overBudget {
            return "Runs ~\(mins) min — longer than your walk"
        }
        let skipped = plan.skippedIndices.count
        let skipNote = skipped > 0 ? " · \(skipped) bonus skipped" : ""
        return "Ends in ~\(mins) min\(skipNote)"
    }

    private func formatDuration(_ seconds: Double) -> String {
        let mins = Int(seconds) / 60
        let secs = Int(seconds) % 60
        return String(format: "%d:%02d", mins, secs)
    }

    // MARK: - Loading

    private func loadManifest() async {
        do {
            manifest = try await APIClient.shared.getManifest(episodeId: episode.id)
        } catch {
            loadError = "This episode was generated before chapters existed. Regenerate it to use walk mode."
        }
    }
}
