(function () {
  const busIcon = window.busIcon;

  window.createCustomMap = function (
    mapContainerId,
    lat,
    lng,
    destLat = null,
    destLng = null,
    busData = null,
    updateInterval = 5000,
    busDataUrl = null,
  ) {
    const mapElement = document.getElementById(mapContainerId);
    if (!mapElement) {
      console.error(`Element with id ${mapContainerId} not found.`);
      return;
    }

    console.log(`Initializing map with ID: ${mapContainerId}`);
    console.log(`Latitude: ${lat}, Longitude: ${lng}`);

    const mapLocation = { lat: lat, lng: lng };

    const grayscaleStyle = [
      { elementType: "geometry", stylers: [{ color: "#ebe3cd" }] },
      { elementType: "labels.text.fill", stylers: [{ color: "#523735" }] },
      { elementType: "labels.text.stroke", stylers: [{ color: "#f5f1e6" }] },
      {
        featureType: "administrative",
        elementType: "geometry.stroke",
        stylers: [{ color: "#c9b2a6" }],
      },
      {
        featureType: "administrative.land_parcel",
        elementType: "geometry.stroke",
        stylers: [{ color: "#dcd2be" }],
      },
      {
        featureType: "administrative.land_parcel",
        elementType: "labels.text.fill",
        stylers: [{ color: "#ae9e90" }],
      },
      {
        featureType: "landscape.natural",
        elementType: "geometry",
        stylers: [{ color: "#dfd2ae" }],
      },
      {
        featureType: "poi",
        elementType: "geometry",
        stylers: [{ color: "#dfd2ae" }],
      },
      {
        featureType: "poi",
        elementType: "labels.text.fill",
        stylers: [{ color: "#93817c" }],
      },
      {
        featureType: "poi.park",
        elementType: "geometry.fill",
        stylers: [{ color: "#a5b076" }],
      },
      {
        featureType: "poi.park",
        elementType: "labels.text.fill",
        stylers: [{ color: "#447530" }],
      },
      {
        featureType: "road",
        elementType: "geometry",
        stylers: [{ color: "#f5f1e6" }],
      },
      {
        featureType: "road.arterial",
        elementType: "geometry",
        stylers: [{ color: "#fdfcf8" }],
      },
      {
        featureType: "road.highway",
        elementType: "geometry",
        stylers: [{ color: "#f8c967" }],
      },
      {
        featureType: "road.highway",
        elementType: "geometry.stroke",
        stylers: [{ color: "#e9bc62" }],
      },
      {
        featureType: "road.highway.controlled_access",
        elementType: "geometry",
        stylers: [{ color: "#e98d58" }],
      },
      {
        featureType: "road.highway.controlled_access",
        elementType: "geometry.stroke",
        stylers: [{ color: "#db8555" }],
      },
      {
        featureType: "road.local",
        elementType: "labels.text.fill",
        stylers: [{ color: "#806b63" }],
      },
      {
        featureType: "transit.line",
        elementType: "geometry",
        stylers: [{ color: "#dfd2ae" }],
      },
      {
        featureType: "transit.line",
        elementType: "labels.text.fill",
        stylers: [{ color: "#8f7d77" }],
      },
      {
        featureType: "transit.line",
        elementType: "labels.text.stroke",
        stylers: [{ color: "#ebe3cd" }],
      },
      {
        featureType: "transit.station",
        elementType: "geometry",
        stylers: [{ color: "#dfd2ae" }],
      },
      {
        featureType: "water",
        elementType: "geometry.fill",
        stylers: [{ color: "#b9d3c2" }],
      },
      {
        featureType: "water",
        elementType: "labels.text.fill",
        stylers: [{ color: "#92998d" }],
      },
    ];

    const mapInstance = new google.maps.Map(mapElement, {
      zoom: 12,
      center: mapLocation,
      gestureHandling: "auto",
      disableDefaultUI: true,
      styles: grayscaleStyle,
    });

    new google.maps.Marker({
      position: mapLocation,
      map: mapInstance,
      title: "Your Location",
    });

    if (destLat !== null && destLng !== null) {
      console.log(
        `Destination Latitude: ${destLat}, Destination Longitude: ${destLng}`,
      );
      const destinationLocation = { lat: destLat, lng: destLng };

      new google.maps.Marker({
        position: destinationLocation,
        map: mapInstance,
        title: "Destination",
      });

      const directionsService = new google.maps.DirectionsService();
      const directionsRenderer = new google.maps.DirectionsRenderer();
      directionsRenderer.setMap(mapInstance);

      const request = {
        origin: mapLocation,
        destination: destinationLocation,
        travelMode: google.maps.TravelMode.TRANSIT,
      };

      directionsService.route(request, (result, status) => {
        if (status === google.maps.DirectionsStatus.OK) {
          directionsRenderer.setDirections(result);
        } else {
          console.error("Directions request failed due to " + status);
        }
      });
    } else {
      console.log("Single location provided. Showing only this location.");
    }

    const transitLayer = new google.maps.TransitLayer();
    transitLayer.setMap(mapInstance);

    const markers = new Map(); // Use a Map for better performance in finding and updating markers

    function animate(marker, newPosition, duration) {
      const startPos = marker.getPosition();
      const startTime = Date.now();

      function updateMarkerPosition() {
        const now = Date.now();
        const elapsed = now - startTime;
        const progress = Math.min(elapsed / duration, 1);

        const lat =
          startPos.lat() + (newPosition.lat - startPos.lat()) * progress;
        const lng =
          startPos.lng() + (newPosition.lng - startPos.lng()) * progress;

        marker.setPosition(new google.maps.LatLng(lat, lng));

        if (progress < 1) {
          requestAnimationFrame(updateMarkerPosition);
        }
      }

      updateMarkerPosition();
    }

    function addBusMarkers(busData) {
      if (busData && Array.isArray(busData)) {
        console.log(`Adding ${busData.length} bus markers to the map.`);

        busData.forEach((bus) => {
          const busPosition = {
            lat: parseFloat(bus.GPS_Latitude),
            lng: parseFloat(bus.GPS_Longitude),
          };

          let busMarker = markers.get(bus.Vehicle_No);

          if (busMarker) {
            // Animate existing marker to new position
            animate(busMarker, busPosition, 2000);
          } else {
            // Create new marker and add to the map
            busMarker = new google.maps.Marker({
              position: busPosition,
              map: mapInstance,
              title: bus.Vehicle_No,
              icon: {
                url:
                  busIcon ||
                  "https://maps.google.com/mapfiles/ms/icons/red-dot.png",
                scaledSize: new google.maps.Size(32, 32),
              },
            });

            const infoWindow = new google.maps.InfoWindow({
              content: `<div><h5>${bus.Vehicle_No}</h5></div>`,
            });

            busMarker.addListener("click", () => {
              infoWindow.open(mapInstance, busMarker);
            });

            markers.set(bus.Vehicle_No, busMarker); // Store the marker reference
          }
        });

        // Remove markers that are no longer in the new busData
        markers.forEach((marker, vehicleNo) => {
          if (!busData.find((bus) => bus.Vehicle_No === vehicleNo)) {
            marker.setMap(null);
            markers.delete(vehicleNo);
          }
        });
      } else {
        console.log("No bus data provided.");
      }
    }

    if (busData) {
      addBusMarkers(busData);
    }

    if (busDataUrl) {
      setInterval(async () => {
        try {
          const response = await fetch(busDataUrl);
          if (!response.ok) {
            throw new Error("Network response was not ok");
          }
          const newBusData = await response.json();
          addBusMarkers(newBusData);
          console.log("Updated bus data");
        } catch (error) {
          console.error("Error fetching bus data:", error);
        }
      }, updateInterval);
    }
  };
})();
