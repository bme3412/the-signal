import SwiftUI

protocol StyleDimension: RawRepresentable, CaseIterable, Identifiable, Hashable where RawValue == String, AllCases: RandomAccessCollection {
    var displayName: String { get }
    var icon: String { get }
    var shortDescription: String { get }
    var color: Color { get }
}

extension Depth: StyleDimension {}
extension Tone: StyleDimension {}
extension Lens: StyleDimension {}
extension Pacing: StyleDimension {}
extension Humor: StyleDimension {}
extension Audience: StyleDimension {}
extension Structure: StyleDimension {}
extension Closer: StyleDimension {}

struct DimensionRow<T: StyleDimension>: View {
    let title: String
    @Binding var selection: T

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text(title.uppercased())
                .font(.caption.weight(.bold))
                .foregroundStyle(Color.textMuted)
                .tracking(1)

            ScrollView(.horizontal, showsIndicators: false) {
                HStack(spacing: 8) {
                    ForEach(Array(T.allCases), id: \.self) { option in
                        pillButton(for: option)
                    }
                }
            }

            if !selection.shortDescription.isEmpty {
                Text(selection.shortDescription)
                    .font(.caption)
                    .foregroundStyle(Color.textSecondary)
                    .transition(.opacity)
            }
        }
    }

    private func pillButton(for option: T) -> some View {
        let isSelected = selection == option
        return Button {
            withAnimation(.snappy(duration: 0.2)) {
                selection = option
            }
        } label: {
            HStack(spacing: 5) {
                Image(systemName: option.icon)
                    .font(.caption2)
                Text(option.displayName)
                    .font(.caption.weight(.medium))
            }
            .padding(.horizontal, 12)
            .padding(.vertical, 8)
            .background(
                isSelected ? option.color.opacity(0.2) : Color.clear,
                in: .capsule
            )
            .overlay(
                Capsule()
                    .strokeBorder(
                        isSelected ? option.color : Color.border,
                        lineWidth: 1
                    )
            )
            .foregroundStyle(isSelected ? option.color : Color.textSecondary)
        }
        .buttonStyle(.plain)
    }
}
