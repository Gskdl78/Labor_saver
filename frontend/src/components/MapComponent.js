import React, { useEffect, useRef } from 'react';
import { Box, Typography } from '@mui/material';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

// 修復 Leaflet 圖標問題
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.3/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.3/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.3/images/marker-shadow.png',
});

const MapComponent = ({ userLocation, locations, onLocationClick, selectedLocation }) => {
  const mapRef = useRef(null);
  const mapInstanceRef = useRef(null);
  const markersRef = useRef([]);

  // 初始化地圖
  useEffect(() => {
    if (!mapRef.current) return;

    // 創建地圖實例
    mapInstanceRef.current = L.map(mapRef.current).setView([23.8, 121.0], 8);

    // 添加圖磚層
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '© OpenStreetMap contributors'
    }).addTo(mapInstanceRef.current);

    return () => {
      if (mapInstanceRef.current) {
        mapInstanceRef.current.remove();
        mapInstanceRef.current = null;
      }
    };
  }, []);

  // 清除所有標記
  const clearMarkers = () => {
    markersRef.current.forEach(marker => {
      mapInstanceRef.current.removeLayer(marker);
    });
    markersRef.current = [];
  };

  // 添加用戶位置標記
  useEffect(() => {
    if (!mapInstanceRef.current || !userLocation) return;

    // 清除舊標記
    clearMarkers();

    // 創建用戶位置圖標
    const userIcon = L.divIcon({
      html: `
        <div style="
          background-color: #2196F3;
          width: 20px;
          height: 20px;
          border-radius: 50%;
          border: 3px solid white;
          box-shadow: 0 2px 6px rgba(0,0,0,0.3);
        "></div>
      `,
      className: 'user-location-marker',
      iconSize: [20, 20],
      iconAnchor: [10, 10],
    });

    // 添加用戶位置標記
    const userMarker = L.marker([userLocation.latitude, userLocation.longitude], {
      icon: userIcon
    }).addTo(mapInstanceRef.current);

    userMarker.bindPopup('您的位置').openPopup();
    markersRef.current.push(userMarker);

    // 移動地圖到用戶位置
    mapInstanceRef.current.setView([userLocation.latitude, userLocation.longitude], 12);

  }, [userLocation]);

  // 添加位置標記
  useEffect(() => {
    if (!mapInstanceRef.current || !locations.length) return;

    // 為每個位置創建標記
    locations.forEach((location, index) => {
      if (!location.latitude || !location.longitude) return;

      // 創建位置圖標
      const locationIcon = L.divIcon({
        html: `
          <div style="
            background-color: ${location.type === 'hospital' ? '#f44336' : '#9c27b0'};
            color: white;
            width: 30px;
            height: 30px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 12px;
            font-weight: bold;
            border: 2px solid white;
            box-shadow: 0 2px 6px rgba(0,0,0,0.3);
          ">
            ${location.type === 'hospital' ? '醫' : '勞'}
          </div>
        `,
        className: 'location-marker',
        iconSize: [30, 30],
        iconAnchor: [15, 15],
      });

      // 創建標記
      const marker = L.marker([location.latitude, location.longitude], {
        icon: locationIcon
      }).addTo(mapInstanceRef.current);

      // 創建彈出視窗內容
      const popupContent = `
        <div style="min-width: 200px;">
          <h4 style="margin: 0 0 8px 0; color: #333;">${location.name}</h4>
          <p style="margin: 0 0 4px 0; font-size: 12px; color: #666;">
            <strong>地址：</strong>${location.address}
          </p>
          <p style="margin: 0 0 4px 0; font-size: 12px; color: #666;">
            <strong>電話：</strong>${location.phone}
          </p>
          ${location.distance ? `
            <p style="margin: 0 0 8px 0; font-size: 12px; color: #666;">
              <strong>距離：</strong>${location.distance < 1 ? 
                `${Math.round(location.distance * 1000)}公尺` : 
                `${location.distance.toFixed(1)}公里`
              }
            </p>
          ` : ''}
          <button 
            onclick="window.handleLocationClick(${index})"
            style="
              background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
              color: white;
              border: none;
              padding: 6px 12px;
              border-radius: 4px;
              cursor: pointer;
              font-size: 12px;
            "
          >
            查看詳情
          </button>
        </div>
      `;

      marker.bindPopup(popupContent);
      markersRef.current.push(marker);
    });

    // 如果有位置數據，調整地圖視圖以包含所有標記
    if (locations.length > 0 && userLocation) {
      const group = new L.featureGroup([
        L.marker([userLocation.latitude, userLocation.longitude]),
        ...locations
          .filter(loc => loc.latitude && loc.longitude)
          .map(loc => L.marker([loc.latitude, loc.longitude]))
      ]);
      
      mapInstanceRef.current.fitBounds(group.getBounds().pad(0.1));
    }

    // 設置全域點擊處理函數
    window.handleLocationClick = (index) => {
      if (onLocationClick) {
        onLocationClick(locations[index]);
      }
    };

    return () => {
      // 清理全域函數
      delete window.handleLocationClick;
    };

  }, [locations, onLocationClick, userLocation]);

  // 處理選中位置的地圖跳轉
  useEffect(() => {
    if (!mapInstanceRef.current || !selectedLocation || !selectedLocation.latitude || !selectedLocation.longitude) return;

    // 跳轉到選中位置
    mapInstanceRef.current.setView([selectedLocation.latitude, selectedLocation.longitude], 15);

    // 找到對應的標記並打開彈窗
    const targetIndex = locations.findIndex(loc => 
      loc.latitude === selectedLocation.latitude && 
      loc.longitude === selectedLocation.longitude
    );

    if (targetIndex !== -1 && markersRef.current[targetIndex + 1]) { // +1 因為第一個是用戶位置標記
      markersRef.current[targetIndex + 1].openPopup();
    }

  }, [selectedLocation, locations]);

  return (
    <Box sx={{ position: 'relative', height: '100%', width: '100%' }}>
      <div
        ref={mapRef}
        style={{
          height: '100%',
          width: '100%',
          borderRadius: '8px',
        }}
      />
      {!userLocation && (
        <Box
          sx={{
            position: 'absolute',
            top: '50%',
            left: '50%',
            transform: 'translate(-50%, -50%)',
            textAlign: 'center',
            bgcolor: 'rgba(255, 255, 255, 0.9)',
            p: 2,
            borderRadius: 2,
            zIndex: 1000,
          }}
        >
          <Typography variant="h6" color="text.secondary">
            請先獲取您的位置
          </Typography>
          <Typography variant="body2" color="text.secondary">
            點擊左側的「獲取我的位置」按鈕
          </Typography>
        </Box>
      )}
    </Box>
  );
};

export default MapComponent;
