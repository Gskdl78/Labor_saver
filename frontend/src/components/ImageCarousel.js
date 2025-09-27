import React, { useState, useEffect } from 'react';
import { Box, IconButton } from '@mui/material';
import { ArrowBackIos, ArrowForwardIos } from '@mui/icons-material';

const ImageCarousel = () => {
  const [currentIndex, setCurrentIndex] = useState(0);
  const [isAutoPlaying, setIsAutoPlaying] = useState(true);

  // 圖片路徑（假設圖片已放在 public/images 目錄下）
  const images = [
    {
      src: '/images/image.png',
      alt: '勞災保險服務圖片1',
    },
    {
      src: '/images/image1.png',
      alt: '勞災保險服務圖片2',
    },
    {
      src: '/images/image3.png',
      alt: '勞災保險服務圖片3',
    },
  ];

  // 自動輪播
  useEffect(() => {
    if (!isAutoPlaying) return;

    const interval = setInterval(() => {
      setCurrentIndex((prevIndex) => 
        prevIndex === images.length - 1 ? 0 : prevIndex + 1
      );
    }, 4000); // 每4秒切換一次

    return () => clearInterval(interval);
  }, [images.length, isAutoPlaying]);

  const goToPrevious = () => {
    setIsAutoPlaying(false);
    setCurrentIndex(currentIndex === 0 ? images.length - 1 : currentIndex - 1);
    // 3秒後恢復自動播放
    setTimeout(() => setIsAutoPlaying(true), 3000);
  };

  const goToNext = () => {
    setIsAutoPlaying(false);
    setCurrentIndex(currentIndex === images.length - 1 ? 0 : currentIndex + 1);
    // 3秒後恢復自動播放
    setTimeout(() => setIsAutoPlaying(true), 3000);
  };

  const goToSlide = (index) => {
    setIsAutoPlaying(false);
    setCurrentIndex(index);
    // 3秒後恢復自動播放
    setTimeout(() => setIsAutoPlaying(true), 3000);
  };

  return (
    <Box
      sx={{
        position: 'relative',
        width: '100%',
        height: { xs: '250px', md: '400px' },
        borderRadius: 2,
        overflow: 'hidden',
        boxShadow: '0 8px 32px rgba(0, 0, 0, 0.2)',
      }}
    >
      {/* 圖片容器 */}
      <Box
        sx={{
          display: 'flex',
          width: `${images.length * 100}%`,
          height: '100%',
          transform: `translateX(-${currentIndex * (100 / images.length)}%)`,
          transition: 'transform 0.6s ease-in-out',
        }}
      >
        {images.map((image, index) => (
          <Box
            key={index}
            sx={{
              width: `${100 / images.length}%`,
              height: '100%',
              flexShrink: 0,
            }}
          >
            <img
              src={image.src}
              alt={image.alt}
              style={{
                width: '100%',
                height: '100%',
                objectFit: 'cover',
                display: 'block',
              }}
              onError={(e) => {
                // 如果圖片載入失敗，顯示預設背景
                e.target.style.display = 'none';
                e.target.parentElement.style.background = 'linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%)';
                e.target.parentElement.style.display = 'flex';
                e.target.parentElement.style.alignItems = 'center';
                e.target.parentElement.style.justifyContent = 'center';
                e.target.parentElement.innerHTML = '<div style="color: rgba(255,255,255,0.7); font-size: 18px;">圖片載入中...</div>';
              }}
            />
          </Box>
        ))}
      </Box>

      {/* 左箭頭 */}
      <IconButton
        onClick={goToPrevious}
        sx={{
          position: 'absolute',
          left: 16,
          top: '50%',
          transform: 'translateY(-50%)',
          bgcolor: 'rgba(255, 255, 255, 0.8)',
          color: '#667eea',
          '&:hover': {
            bgcolor: 'rgba(255, 255, 255, 0.9)',
          },
          zIndex: 2,
        }}
      >
        <ArrowBackIos />
      </IconButton>

      {/* 右箭頭 */}
      <IconButton
        onClick={goToNext}
        sx={{
          position: 'absolute',
          right: 16,
          top: '50%',
          transform: 'translateY(-50%)',
          bgcolor: 'rgba(255, 255, 255, 0.8)',
          color: '#667eea',
          '&:hover': {
            bgcolor: 'rgba(255, 255, 255, 0.9)',
          },
          zIndex: 2,
        }}
      >
        <ArrowForwardIos />
      </IconButton>

      {/* 指示點 */}
      <Box
        sx={{
          position: 'absolute',
          bottom: 16,
          left: '50%',
          transform: 'translateX(-50%)',
          display: 'flex',
          gap: 1,
          zIndex: 2,
        }}
      >
        {images.map((_, index) => (
          <Box
            key={index}
            onClick={() => goToSlide(index)}
            sx={{
              width: 12,
              height: 12,
              borderRadius: '50%',
              bgcolor: currentIndex === index 
                ? 'rgba(255, 255, 255, 0.9)' 
                : 'rgba(255, 255, 255, 0.5)',
              cursor: 'pointer',
              transition: 'all 0.3s ease',
              '&:hover': {
                bgcolor: 'rgba(255, 255, 255, 0.8)',
                transform: 'scale(1.2)',
              },
            }}
          />
        ))}
      </Box>

      {/* 自動播放指示器 */}
      {isAutoPlaying && (
        <Box
          sx={{
            position: 'absolute',
            top: 16,
            right: 16,
            bgcolor: 'rgba(0, 0, 0, 0.5)',
            color: 'white',
            px: 2,
            py: 0.5,
            borderRadius: 1,
            fontSize: '0.75rem',
            zIndex: 2,
          }}
        >
          自動播放
        </Box>
      )}
    </Box>
  );
};

export default ImageCarousel;
