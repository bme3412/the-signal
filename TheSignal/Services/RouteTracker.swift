import CoreLocation
import MapKit
import Observation

/// Tracks progress toward a walking destination: destination search, initial
/// walking ETA, and throttled live ETA updates while the walk is underway.
@Observable
final class RouteTracker: NSObject {
    var authorizationStatus: CLAuthorizationStatus = .notDetermined
    var currentLocation: CLLocation?
    var destinationName: String?
    var distanceMeters: Double?
    var etaSeconds: TimeInterval?
    var arrived = false

    private let manager = CLLocationManager()
    private var destination: MKMapItem?
    private var onETAUpdate: ((TimeInterval) -> Void)?
    private var lastETARequest: Date?
    private var lastETALocation: CLLocation?

    static let arrivalRadiusMeters: Double = 30
    static let etaRefreshSeconds: TimeInterval = 30
    static let etaRefreshMeters: Double = 50

    var isAuthorized: Bool {
        authorizationStatus == .authorizedWhenInUse || authorizationStatus == .authorizedAlways
    }

    override init() {
        super.init()
        manager.delegate = self
        manager.desiredAccuracy = kCLLocationAccuracyNearestTenMeters
        authorizationStatus = manager.authorizationStatus
    }

    func requestAuthorization() {
        manager.requestWhenInUseAuthorization()
    }

    // MARK: - Search & ETA

    func searchDestinations(query: String) async throws -> [MKMapItem] {
        let request = MKLocalSearch.Request()
        request.naturalLanguageQuery = query
        if let location = currentLocation {
            request.region = MKCoordinateRegion(
                center: location.coordinate,
                latitudinalMeters: 5_000,
                longitudinalMeters: 5_000
            )
        }
        return try await MKLocalSearch(request: request).start().mapItems
    }

    func walkingETA(to destination: MKMapItem, from location: CLLocation? = nil) async throws -> TimeInterval {
        let request = MKDirections.Request()
        if let location {
            request.source = MKMapItem(placemark: MKPlacemark(coordinate: location.coordinate))
        } else {
            request.source = MKMapItem.forCurrentLocation()
        }
        request.destination = destination
        request.transportType = .walking
        let response = try await MKDirections(request: request).calculateETA()
        return response.expectedTravelTime
    }

    // MARK: - Live Tracking

    func startTracking(destination: MKMapItem, onETAUpdate: @escaping (TimeInterval) -> Void) {
        self.destination = destination
        self.destinationName = destination.name
        self.onETAUpdate = onETAUpdate
        arrived = false
        manager.startUpdatingLocation()
    }

    func stopTracking() {
        manager.stopUpdatingLocation()
        destination = nil
        onETAUpdate = nil
    }

    func distanceText() -> String? {
        guard let meters = distanceMeters else { return nil }
        if arrived { return "arrived" }
        return meters < 1000
            ? "\(Int(meters)) m to go"
            : String(format: "%.1f km to go", meters / 1000)
    }
}

// MARK: - CLLocationManagerDelegate

extension RouteTracker: CLLocationManagerDelegate {
    func locationManagerDidChangeAuthorization(_ manager: CLLocationManager) {
        authorizationStatus = manager.authorizationStatus
        if isAuthorized, destination == nil {
            manager.requestLocation()  // prime currentLocation for search biasing
        }
    }

    func locationManager(_ manager: CLLocationManager, didUpdateLocations locations: [CLLocation]) {
        guard let location = locations.last else { return }
        currentLocation = location
        guard let destination else { return }

        let coord = destination.placemark.coordinate
        let distance = location.distance(from: CLLocation(latitude: coord.latitude, longitude: coord.longitude))
        distanceMeters = distance
        if distance <= Self.arrivalRadiusMeters {
            arrived = true
        }

        // MKDirections is rate-limited; refresh only after real movement and
        // a minimum interval.
        let movedEnough = lastETALocation.map { location.distance(from: $0) >= Self.etaRefreshMeters } ?? true
        let waitedEnough = lastETARequest.map { Date().timeIntervalSince($0) >= Self.etaRefreshSeconds } ?? true
        guard movedEnough, waitedEnough else { return }
        lastETARequest = Date()
        lastETALocation = location

        Task { [weak self] in
            guard let self, let destination = self.destination else { return }
            if let eta = try? await self.walkingETA(to: destination, from: location) {
                self.etaSeconds = eta
                self.onETAUpdate?(eta)
            }
        }
    }

    func locationManager(_ manager: CLLocationManager, didFailWithError error: Error) {
        print("RouteTracker: location error — \(error)")
    }
}
