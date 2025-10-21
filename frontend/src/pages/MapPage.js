import React, { useState, useEffect } from 'react';
import {
  Box,
  Container,
  Typography,
  Paper,
  ToggleButton,
  ToggleButtonGroup,
  Button,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Chip,
  CircularProgress,
  Alert,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Grid,
} from '@mui/material';
import {
  LocalHospital,
  Business,
  MyLocation,
  Phone,
  LocationOn,
  Schedule,
} from '@mui/icons-material';
import { mapAPI } from '../services/api';
import MapComponent from '../components/MapComponent';

const MapPage = () => {
  const [searchType, setSearchType] = useState('hospital');
  const [locations, setLocations] = useState([]);
  const [userLocation, setUserLocation] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [selectedLocation, setSelectedLocation] = useState(null);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [mapSelectedLocation, setMapSelectedLocation] = useState(null);

  // 獲取用戶位置
  const getUserLocation = () => {
    setIsLoading(true);
    setError(null);

    if (!navigator.geolocation) {
      setError('您的瀏覽器不支援地理位置功能');
      setIsLoading(false);
      return;
    }

    navigator.geolocation.getCurrentPosition(
      (position) => {
        const { latitude, longitude } = position.coords;
        setUserLocation({ latitude, longitude });
        searchNearbyLocations(latitude, longitude, searchType);
      },
      (error) => {
        console.error('獲取位置失敗:', error);
        setError('無法獲取您的位置，請檢查瀏覽器設定');
        setIsLoading(false);
      },
      {
        enableHighAccuracy: true,
        timeout: 10000,
        maximumAge: 600000, // 10分鐘
      }
    );
  };

  // 搜索附近位置
  const searchNearbyLocations = async (latitude, longitude, type) => {
    try {
      setIsLoading(true);
      setError(null);
      console.log('搜索附近位置:', { latitude, longitude, type });
      
      const response = await mapAPI.getNearbyLocations(latitude, longitude, type, 50);
      console.log('API響應:', response.data);
      
      if (response.data.success && response.data.locations) {
        console.log('位置數據詳情:', response.data.locations);
        setLocations(response.data.locations);
        console.log('設置位置列表:', response.data.locations.length, '個位置');
        
        // 檢查座標數據
        response.data.locations.forEach((loc, index) => {
          console.log(`位置 ${index + 1}:`, {
            name: loc.name,
            latitude: loc.latitude,
            longitude: loc.longitude,
            type: loc.type
          });
        });
      } else {
        console.error('API返回錯誤:', response.data.error);
        setError(response.data.error || '搜索附近位置失敗');
      }
    } catch (err) {
      console.error('搜索位置失敗:', err);
      setError('搜索附近位置失敗，請稍後再試');
    } finally {
      setIsLoading(false);
    }
  };

  // 處理搜索類型變更
  const handleTypeChange = (event, newType) => {
    if (newType !== null) {
      setSearchType(newType);
      setLocations([]);
      if (userLocation) {
        searchNearbyLocations(userLocation.latitude, userLocation.longitude, newType);
      }
    }
  };

  // 打開位置詳情對話框
  const handleLocationClick = (location) => {
    setSelectedLocation(location);
    setDialogOpen(true);
  };

  // 處理列表項目點擊，跳轉地圖
  const handleListItemClick = (location) => {
    setMapSelectedLocation(location);
    setSelectedLocation(location);
    setDialogOpen(true);
  };

  // 格式化距離
  const formatDistance = (distance) => {
    if (!distance) return '';
    return distance < 1 ? `${Math.round(distance * 1000)}公尺` : `${distance.toFixed(1)}公里`;
  };

  // 獲取位置圖標
  const getLocationIcon = (type) => {
    return type === 'hospital' ? <LocalHospital color="error" /> : <Business color="primary" />;
  };

  // 獲取位置類型名稱
  const getLocationTypeName = (type) => {
    return type === 'hospital' ? '醫院' : '勞保局辦事處';
  };

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Typography
        variant="h4"
        component="h1"
        gutterBottom
        textAlign="center"
        sx={{ mb: 4, fontWeight: 600 }}
      >
        地圖搜索
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      <Grid container spacing={3}>
        {/* 左側控制面板 */}
        <Grid item xs={12} md={4}>
          <Paper elevation={3} sx={{ p: 3, mb: 3 }}>
            <Typography variant="h6" gutterBottom>
              搜索選項
            </Typography>

            {/* 搜索類型選擇 */}
            <Box sx={{ mb: 3 }}>
              <Typography variant="subtitle1" gutterBottom>
                選擇搜索類型：
              </Typography>
              <ToggleButtonGroup
                value={searchType}
                exclusive
                onChange={handleTypeChange}
                fullWidth
                size="small"
              >
                <ToggleButton value="hospital">
                  <LocalHospital sx={{ mr: 1 }} />
                  合格醫院
                </ToggleButton>
                <ToggleButton value="labor_office">
                  <Business sx={{ mr: 1 }} />
                  勞保局
                </ToggleButton>
              </ToggleButtonGroup>
            </Box>

            {/* 定位按鈕 */}
            <Button
              fullWidth
              variant="contained"
              startIcon={<MyLocation />}
              onClick={getUserLocation}
              disabled={isLoading}
              sx={{ mb: 2 }}
            >
              {isLoading ? '定位中...' : '獲取我的位置'}
            </Button>

            {userLocation && (
              <Chip
                label={`已定位：${userLocation.latitude.toFixed(4)}, ${userLocation.longitude.toFixed(4)}`}
                color="success"
                size="small"
                sx={{ mb: 2 }}
              />
            )}
          </Paper>

          {/* 搜索結果列表 */}
          <Paper elevation={3} sx={{ maxHeight: '500px', overflow: 'auto' }}>
            <Box sx={{ p: 2, borderBottom: '1px solid #e0e0e0' }}>
              <Typography variant="h6">
                {getLocationTypeName(searchType)}列表
                {locations.length > 0 && (
                  <Chip
                    label={`${locations.length} 個結果`}
                    size="small"
                    sx={{ ml: 1 }}
                  />
                )}
              </Typography>
            </Box>

            {isLoading ? (
              <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
                <CircularProgress />
              </Box>
            ) : locations.length > 0 ? (
              <List>
                {locations.map((location, index) => (
                  <ListItem
                    key={index}
                    button
                    onClick={() => handleListItemClick(location)}
                    sx={{
                      borderBottom: index < locations.length - 1 ? '1px solid #f0f0f0' : 'none',
                    }}
                  >
                    <ListItemIcon>
                      {getLocationIcon(location.type)}
                    </ListItemIcon>
                    <ListItemText
                      primary={location.name}
                      secondary={
                        <Box>
                          <Typography variant="body2" color="text.secondary">
                            {location.address}
                          </Typography>
                          {location.distance && (
                            <Chip
                              label={formatDistance(location.distance)}
                              size="small"
                              color="primary"
                              sx={{ mt: 0.5 }}
                            />
                          )}
                        </Box>
                      }
                    />
                  </ListItem>
                ))}
              </List>
            ) : userLocation ? (
              <Box sx={{ p: 3, textAlign: 'center' }}>
                <Typography color="text.secondary">
                  附近沒有找到{getLocationTypeName(searchType)}
                </Typography>
              </Box>
            ) : (
              <Box sx={{ p: 3, textAlign: 'center' }}>
                <Typography color="text.secondary">
                  請先獲取您的位置以搜索附近的{getLocationTypeName(searchType)}
                </Typography>
              </Box>
            )}
          </Paper>
        </Grid>

        {/* 右側地圖 */}
        <Grid item xs={12} md={8}>
          <Paper elevation={3} sx={{ height: '600px', overflow: 'hidden' }}>
            <MapComponent
              userLocation={userLocation}
              locations={locations}
              onLocationClick={handleLocationClick}
              selectedLocation={mapSelectedLocation}
            />
          </Paper>
        </Grid>
      </Grid>

      {/* 位置詳情對話框 */}
      <Dialog
        open={dialogOpen}
        onClose={() => {
          setDialogOpen(false);
          // 不清除 selectedLocation 和 mapSelectedLocation，保持地圖位置
        }}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            {selectedLocation && getLocationIcon(selectedLocation.type)}
            {selectedLocation?.name}
          </Box>
        </DialogTitle>
        <DialogContent>
          {selectedLocation && (
            <Box>
              <Box sx={{ mb: 2 }}>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  地址
                </Typography>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <LocationOn fontSize="small" />
                  <Typography>{selectedLocation.address}</Typography>
                </Box>
              </Box>

              <Box sx={{ mb: 2 }}>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  電話
                </Typography>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <Phone fontSize="small" />
                  <Typography>{selectedLocation.phone}</Typography>
                </Box>
              </Box>

              {selectedLocation.distance && (
                <Box sx={{ mb: 2 }}>
                  <Typography variant="body2" color="text.secondary" gutterBottom>
                    距離
                  </Typography>
                  <Chip
                    label={formatDistance(selectedLocation.distance)}
                    color="primary"
                    size="small"
                  />
                </Box>
              )}

              {selectedLocation.additional_info && (
                <Box>
                  <Typography variant="body2" color="text.secondary" gutterBottom>
                    其他資訊
                  </Typography>
                  {selectedLocation.additional_info.counter_hours && (
                    <Box sx={{ mb: 1 }}>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <Schedule fontSize="small" />
                        <Typography variant="body2">
                          櫃台服務時間：{selectedLocation.additional_info.counter_hours}
                        </Typography>
                      </Box>
                    </Box>
                  )}
                  {selectedLocation.additional_info.phone_hours && (
                    <Box sx={{ mb: 1 }}>
                      <Typography variant="body2" sx={{ ml: 3 }}>
                        電話服務時間：{selectedLocation.additional_info.phone_hours}
                      </Typography>
                    </Box>
                  )}
                  {selectedLocation.additional_info.evaluation_result && (
                    <Box sx={{ mb: 1 }}>
                      <Typography variant="body2">
                        評鑑結果：{selectedLocation.additional_info.evaluation_result}
                      </Typography>
                    </Box>
                  )}
                  {selectedLocation.additional_info.teaching_hospital && (
                    <Box sx={{ mb: 1 }}>
                      <Typography variant="body2">
                        教學醫院：{selectedLocation.additional_info.teaching_hospital}
                      </Typography>
                    </Box>
                  )}
                </Box>
              )}
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDialogOpen(false)}>關閉</Button>
          {selectedLocation?.phone && (
            <Button
              variant="contained"
              href={`tel:${selectedLocation.phone}`}
              startIcon={<Phone />}
            >
              撥打電話
            </Button>
          )}
        </DialogActions>
      </Dialog>
    </Container>
  );
};

export default MapPage;
