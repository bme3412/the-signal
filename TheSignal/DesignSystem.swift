import SwiftUI

extension Color {
    static let background = Color(hex: 0x09090B)
    static let surface = Color(hex: 0x111113)
    static let border = Color(hex: 0x27272A)
    static let textPrimary = Color(hex: 0xFAFAFA)
    static let textSecondary = Color(hex: 0xA1A1AA)
    static let textMuted = Color(hex: 0x52525B)
    static let accentBlue = Color(hex: 0x0A84FF)
    static let accentPurple = Color(hex: 0xBF5AF2)
    // .green, .orange, .red use system colors for dynamic range
}

extension Color {
    init(hex: UInt, opacity: Double = 1.0) {
        self.init(
            .sRGB,
            red: Double((hex >> 16) & 0xFF) / 255,
            green: Double((hex >> 8) & 0xFF) / 255,
            blue: Double(hex & 0xFF) / 255,
            opacity: opacity
        )
    }

    init?(hex string: String) {
        var hexSanitized = string.trimmingCharacters(in: .whitespacesAndNewlines)
        hexSanitized = hexSanitized.replacingOccurrences(of: "#", with: "")

        guard hexSanitized.count == 6,
              let int = UInt64(hexSanitized, radix: 16) else {
            return nil
        }

        let r = Double((int >> 16) & 0xFF) / 255.0
        let g = Double((int >> 8) & 0xFF) / 255.0
        let b = Double(int & 0xFF) / 255.0

        self.init(red: r, green: g, blue: b)
    }
}

extension Font {
    static func mono(_ style: Font.TextStyle, weight: Font.Weight = .regular) -> Font {
        .system(style, design: .monospaced).weight(weight)
    }
}
