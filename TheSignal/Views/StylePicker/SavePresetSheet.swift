import SwiftUI
import SwiftData

struct SavePresetSheet: View {
    @Environment(\.modelContext) private var modelContext
    @Environment(\.dismiss) private var dismiss

    let config: StyleConfig

    @State private var name = ""
    @State private var selectedIcon = "star.fill"
    @State private var selectedColor = "#007AFF"

    private let iconOptions = [
        "star.fill", "heart.fill", "bolt.fill", "flame.fill",
        "sparkles", "sun.max.fill", "moon.fill", "cloud.fill"
    ]

    private let colorOptions = [
        "#007AFF", "#34C759", "#FF9500", "#FF3B30",
        "#AF52DE", "#5856D6", "#00C7BE", "#FF2D55"
    ]

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(spacing: 24) {
                    nameSection
                    iconSection
                    colorSection
                    previewSection
                }
                .padding()
            }
            .background(Color.background)
            .navigationTitle("Save Preset")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Cancel") { dismiss() }
                }
                ToolbarItem(placement: .confirmationAction) {
                    Button("Save") {
                        savePreset()
                        dismiss()
                    }
                    .fontWeight(.semibold)
                }
            }
        }
        .presentationDetents([.medium])
        .presentationDragIndicator(.visible)
    }

    private var nameSection: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("NAME")
                .font(.caption.weight(.bold))
                .foregroundStyle(Color.textMuted)
                .tracking(1)

            TextField("My Preset", text: $name)
                .textFieldStyle(.plain)
                .padding()
                .background(Color.surface, in: .rect(cornerRadius: 10))
        }
    }

    private var iconSection: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("ICON")
                .font(.caption.weight(.bold))
                .foregroundStyle(Color.textMuted)
                .tracking(1)

            LazyVGrid(columns: Array(repeating: .init(.flexible()), count: 4), spacing: 12) {
                ForEach(iconOptions, id: \.self) { icon in
                    Button {
                        selectedIcon = icon
                    } label: {
                        Image(systemName: icon)
                            .font(.title2)
                            .foregroundStyle(selectedIcon == icon ? currentColor : Color.textSecondary)
                            .frame(width: 50, height: 50)
                            .background(
                                selectedIcon == icon ? currentColor.opacity(0.15) : Color.surface,
                                in: .rect(cornerRadius: 10)
                            )
                            .overlay(
                                RoundedRectangle(cornerRadius: 10)
                                    .strokeBorder(selectedIcon == icon ? currentColor : Color.border)
                            )
                    }
                    .buttonStyle(.plain)
                }
            }
        }
    }

    private var colorSection: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("COLOR")
                .font(.caption.weight(.bold))
                .foregroundStyle(Color.textMuted)
                .tracking(1)

            LazyVGrid(columns: Array(repeating: .init(.flexible()), count: 4), spacing: 12) {
                ForEach(colorOptions, id: \.self) { hex in
                    let color = Color(hex: hex) ?? .blue
                    Button {
                        selectedColor = hex
                    } label: {
                        Circle()
                            .fill(color)
                            .frame(width: 40, height: 40)
                            .overlay(
                                Circle()
                                    .strokeBorder(.white, lineWidth: selectedColor == hex ? 3 : 0)
                            )
                            .shadow(color: selectedColor == hex ? color.opacity(0.5) : .clear, radius: 4)
                    }
                    .buttonStyle(.plain)
                }
            }
        }
    }

    private var previewSection: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("PREVIEW")
                .font(.caption.weight(.bold))
                .foregroundStyle(Color.textMuted)
                .tracking(1)

            HStack(spacing: 12) {
                Image(systemName: selectedIcon)
                    .font(.title2)
                    .foregroundStyle(currentColor)

                VStack(alignment: .leading, spacing: 2) {
                    Text(name.isEmpty ? "My Preset" : name)
                        .font(.subheadline.weight(.semibold))
                        .foregroundStyle(Color.textPrimary)
                    Text("Custom preset")
                        .font(.caption2)
                        .foregroundStyle(Color.textSecondary)
                }

                Spacer()
            }
            .padding()
            .background(currentColor.opacity(0.1), in: .rect(cornerRadius: 12))
            .overlay(
                RoundedRectangle(cornerRadius: 12)
                    .strokeBorder(currentColor.opacity(0.5))
            )
        }
    }

    private var currentColor: Color {
        Color(hex: selectedColor) ?? .blue
    }

    private func savePreset() {
        let preset = SavedPreset(
            name: name.isEmpty ? "My Preset" : name,
            icon: selectedIcon,
            colorHex: selectedColor,
            config: config
        )
        modelContext.insert(preset)
    }
}
