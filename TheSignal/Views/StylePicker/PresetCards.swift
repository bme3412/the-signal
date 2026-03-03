import SwiftUI
import SwiftData

struct PresetCards: View {
    @Binding var style: StyleConfig
    @Environment(\.modelContext) private var modelContext
    @Query(sort: \SavedPreset.createdAt, order: .reverse)
    private var savedPresets: [SavedPreset]

    @State private var showingSaveSheet = false

    private var recentPresets: [SavedPreset] {
        savedPresets
            .filter { $0.lastUsedAt != nil }
            .sorted { ($0.lastUsedAt ?? .distantPast) > ($1.lastUsedAt ?? .distantPast) }
            .prefix(3)
            .map { $0 }
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            if !recentPresets.isEmpty {
                recentSection
            }

            builtInSection

            if !savedPresets.isEmpty {
                customSection
            }
        }
    }

    private var recentSection: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("RECENT")
                .font(.caption.weight(.bold))
                .foregroundStyle(Color.textMuted)
                .tracking(1)

            ScrollView(.horizontal, showsIndicators: false) {
                HStack(spacing: 10) {
                    ForEach(recentPresets) { preset in
                        savedPresetCard(preset, compact: true)
                    }
                }
            }
        }
    }

    private var builtInSection: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Text("PRESETS")
                    .font(.caption.weight(.bold))
                    .foregroundStyle(Color.textMuted)
                    .tracking(1)
                Spacer()
                Button {
                    showingSaveSheet = true
                } label: {
                    Label("Save Current", systemImage: "plus.circle")
                        .font(.caption)
                        .foregroundStyle(Color.accentBlue)
                }
            }

            ScrollView(.horizontal, showsIndicators: false) {
                HStack(spacing: 10) {
                    ForEach(StyleConfig.presets) { preset in
                        presetCard(preset)
                    }
                }
            }
        }
        .sheet(isPresented: $showingSaveSheet) {
            SavePresetSheet(config: style)
        }
    }

    private var customSection: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("SAVED")
                .font(.caption.weight(.bold))
                .foregroundStyle(Color.textMuted)
                .tracking(1)

            ScrollView(.horizontal, showsIndicators: false) {
                HStack(spacing: 10) {
                    ForEach(savedPresets) { preset in
                        savedPresetCard(preset)
                    }
                }
            }
        }
    }

    private func savedPresetCard(_ preset: SavedPreset, compact: Bool = false) -> some View {
        let isActive = style == preset.config
        let color = Color(hex: preset.colorHex) ?? .blue

        return Button {
            withAnimation(.snappy(duration: 0.3)) {
                style = preset.config
                preset.recordUsage()
            }
        } label: {
            VStack(alignment: .leading, spacing: compact ? 4 : 6) {
                Image(systemName: preset.icon)
                    .font(compact ? .caption : .title3)
                    .foregroundStyle(color)

                Text(preset.name)
                    .font(compact ? .caption.weight(.medium) : .subheadline.weight(.semibold))
                    .foregroundStyle(Color.textPrimary)
                    .lineLimit(1)

                if !compact {
                    Text("Custom preset")
                        .font(.caption2)
                        .foregroundStyle(Color.textSecondary)
                }
            }
            .frame(width: compact ? 80 : 110, alignment: .leading)
            .padding(compact ? 8 : 12)
            .background(
                isActive ? color.opacity(0.12) : Color.surface,
                in: .rect(cornerRadius: compact ? 8 : 12)
            )
            .overlay(
                RoundedRectangle(cornerRadius: compact ? 8 : 12)
                    .strokeBorder(isActive ? color : Color.border, lineWidth: isActive ? 1.5 : 1)
            )
        }
        .buttonStyle(.plain)
        .contextMenu {
            Button(role: .destructive) {
                modelContext.delete(preset)
            } label: {
                Label("Delete", systemImage: "trash")
            }
        }
    }

    private func presetCard(_ preset: StylePreset) -> some View {
        let isActive = style == preset.config
        return Button {
            withAnimation(.snappy(duration: 0.3)) {
                style = preset.config
            }
        } label: {
            VStack(alignment: .leading, spacing: 6) {
                Image(systemName: preset.icon)
                    .font(.title3)
                    .foregroundStyle(
                        .linearGradient(
                            colors: preset.gradient,
                            startPoint: .topLeading,
                            endPoint: .bottomTrailing
                        )
                    )

                Text(preset.name)
                    .font(.subheadline.weight(.semibold))
                    .foregroundStyle(Color.textPrimary)

                Text(preset.subtitle)
                    .font(.caption2)
                    .foregroundStyle(Color.textSecondary)
                    .lineLimit(2)
            }
            .frame(width: 130, alignment: .leading)
            .padding(12)
            .background(
                isActive
                    ? AnyShapeStyle(.linearGradient(colors: preset.gradient.map { $0.opacity(0.12) }, startPoint: .topLeading, endPoint: .bottomTrailing))
                    : AnyShapeStyle(Color.surface),
                in: .rect(cornerRadius: 12)
            )
            .overlay(
                RoundedRectangle(cornerRadius: 12)
                    .strokeBorder(
                        isActive
                            ? AnyShapeStyle(.linearGradient(colors: preset.gradient, startPoint: .topLeading, endPoint: .bottomTrailing))
                            : AnyShapeStyle(Color.border),
                        lineWidth: isActive ? 1.5 : 1
                    )
            )
        }
        .buttonStyle(.plain)
    }
}
