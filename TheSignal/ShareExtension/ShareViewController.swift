import UIKit
import UniformTypeIdentifiers

class ShareViewController: UIViewController {
    private let appGroupID = "group.com.thesignal.shared"

    override func viewDidLoad() {
        super.viewDidLoad()
        view.backgroundColor = UIColor(red: 0.035, green: 0.035, blue: 0.043, alpha: 1)
        showConfirmation()
        extractAndSave()
    }

    private func extractAndSave() {
        guard let items = extensionContext?.inputItems as? [NSExtensionItem] else {
            dismiss()
            return
        }

        for item in items {
            guard let attachments = item.attachments else { continue }
            for attachment in attachments {
                if attachment.hasItemConformingToTypeIdentifier(UTType.url.identifier) {
                    attachment.loadItem(forTypeIdentifier: UTType.url.identifier, options: nil) { [weak self] data, _ in
                        if let url = data as? URL {
                            self?.saveURL(url.absoluteString)
                        } else if let data = data as? Data, let url = URL(dataRepresentation: data, relativeTo: nil) {
                            self?.saveURL(url.absoluteString)
                        }
                        DispatchQueue.main.asyncAfter(deadline: .now() + 1.5) {
                            self?.dismiss()
                        }
                    }
                    return
                }

                if attachment.hasItemConformingToTypeIdentifier(UTType.plainText.identifier) {
                    attachment.loadItem(forTypeIdentifier: UTType.plainText.identifier, options: nil) { [weak self] data, _ in
                        if let text = data as? String, let url = URL(string: text), url.scheme != nil {
                            self?.saveURL(text)
                        }
                        DispatchQueue.main.asyncAfter(deadline: .now() + 1.5) {
                            self?.dismiss()
                        }
                    }
                    return
                }
            }
        }

        DispatchQueue.main.asyncAfter(deadline: .now() + 1.5) { [weak self] in
            self?.dismiss()
        }
    }

    private func saveURL(_ urlString: String) {
        guard let defaults = UserDefaults(suiteName: appGroupID) else { return }
        var pending = defaults.stringArray(forKey: "pendingURLs") ?? []
        if !pending.contains(urlString) {
            pending.append(urlString)
            defaults.set(pending, forKey: "pendingURLs")
        }
    }

    private func showConfirmation() {
        let container = UIView()
        container.translatesAutoresizingMaskIntoConstraints = false

        let icon = UIImageView(image: UIImage(systemName: "checkmark.circle.fill"))
        icon.tintColor = UIColor(red: 0.04, green: 0.52, blue: 1.0, alpha: 1)
        icon.translatesAutoresizingMaskIntoConstraints = false
        icon.contentMode = .scaleAspectFit

        let label = UILabel()
        label.text = "Added to The Signal"
        label.textColor = .white
        label.font = .systemFont(ofSize: 17, weight: .semibold)
        label.translatesAutoresizingMaskIntoConstraints = false

        let subtitle = UILabel()
        subtitle.text = "Will appear in your queue"
        subtitle.textColor = UIColor(white: 0.6, alpha: 1)
        subtitle.font = .systemFont(ofSize: 13)
        subtitle.translatesAutoresizingMaskIntoConstraints = false

        let stack = UIStackView(arrangedSubviews: [icon, label, subtitle])
        stack.axis = .vertical
        stack.alignment = .center
        stack.spacing = 8
        stack.translatesAutoresizingMaskIntoConstraints = false

        view.addSubview(stack)
        NSLayoutConstraint.activate([
            icon.widthAnchor.constraint(equalToConstant: 48),
            icon.heightAnchor.constraint(equalToConstant: 48),
            stack.centerXAnchor.constraint(equalTo: view.centerXAnchor),
            stack.centerYAnchor.constraint(equalTo: view.centerYAnchor),
        ])
    }

    private func dismiss() {
        extensionContext?.completeRequest(returningItems: nil)
    }
}
