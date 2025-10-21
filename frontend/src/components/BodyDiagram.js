import React, { useState } from 'react';
import {
  Box,
  Typography,
  ToggleButton,
  ToggleButtonGroup,
  Paper,
  Chip,
} from '@mui/material';
import { Male, Female } from '@mui/icons-material';

const BodyDiagram = ({ selectedBodyPart, onBodyPartClick }) => {
  const [gender, setGender] = useState('male');

  // 根據圖片上的標註位置定義可點擊區域（精確調整坐標）
  const bodyParts = [
    // 左側標註
    { name: '眼', x: 11, y: 19, width: 50 },
    { name: '嘴巴', x: 8, y: 25, width: 60 },
    { name: '右手臂', x: 5, y: 37, width: 70 },
    { name: '腹部', x: 7, y: 51, width: 60 },
    { name: '右手掌', x: 5, y: 62, width: 70 },
    { name: '右腳', x: 8, y: 78, width: 60 },
    { name: '右腳趾', x: 4, y: 93, width: 70 },
    
    // 右側標註
    { name: '頭', x: 88, y: 14, width: 50 },
    { name: '耳朵', x: 88, y: 21, width: 60 },
    { name: '胸', x: 88, y: 35, width: 50 },
    { name: '左手臂', x: 88, y: 42, width: 70 },
    { name: '左手掌', x: 88, y: 61, width: 70 },
    { name: '左腳', x: 88, y: 78, width: 60 },
    { name: '左腳趾', x: 88, y: 93, width: 70 },
  ];

  const handleGenderChange = (event, newGender) => {
    if (newGender !== null) {
      setGender(newGender);
    }
  };

  const handleBodyPartClick = (partName) => {
    if (onBodyPartClick) {
      onBodyPartClick(partName);
    }
  };

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', width: '100%' }}>
      {/* 性別選擇 */}
      <Box sx={{ mb: 3, width: '100%', display: 'flex', justifyContent: 'center' }}>
        <ToggleButtonGroup
          value={gender}
          exclusive
          onChange={handleGenderChange}
          aria-label="性別選擇"
          sx={{
            '& .MuiToggleButton-root': {
              px: 4,
              py: 1.5,
              fontSize: '16px',
              fontWeight: 500,
            },
          }}
        >
          <ToggleButton value="male" aria-label="男性">
            <Male sx={{ mr: 1 }} />
            男性
          </ToggleButton>
          <ToggleButton value="female" aria-label="女性">
            <Female sx={{ mr: 1 }} />
            女性
          </ToggleButton>
        </ToggleButtonGroup>
      </Box>

      <Typography
        variant="subtitle1"
        textAlign="center"
        color="text.secondary"
        sx={{ mb: 3, fontWeight: 500 }}
      >
        點擊圖片上的器官名稱選擇受傷部位
      </Typography>

      {/* 人體圖片容器 */}
      <Paper
        elevation={3}
        sx={{
          width: '100%',
          maxWidth: '700px',
          p: 3,
          backgroundColor: '#f8f9fa',
          position: 'relative',
        }}
      >
        <Box
          sx={{
            position: 'relative',
            width: '100%',
            maxWidth: '600px',
            margin: '0 auto',
          }}
        >
          {/* 人體圖片 */}
          <Box
            component="img"
            src={gender === 'male' ? '/男_new.png' : '/女_new.png'}
            alt={gender === 'male' ? '男性人體圖' : '女性人體圖'}
            sx={{
              width: '100%',
              height: 'auto',
              display: 'block',
            }}
          />

          {/* 可點擊的透明區域 */}
          {bodyParts.map((part) => {
            const isSelected = selectedBodyPart === part.name;
            return (
              <Box
                key={part.name}
                onClick={() => handleBodyPartClick(part.name)}
                sx={{
                  position: 'absolute',
                  left: `${part.x}%`,
                  top: `${part.y}%`,
                  transform: 'translate(-50%, -50%)',
                  cursor: 'pointer',
                  padding: '8px 14px',
                  minWidth: `${part.width}px`,
                  height: '32px',
                  
                  // 完全透明，無任何背景
                  backgroundColor: 'transparent',
                  border: 'none',
                  
                  transition: 'transform 0.15s ease',
                  
                  // hover 時也保持透明，只有輕微放大效果
                  '&:hover': {
                    transform: 'translate(-50%, -50%) scale(1.05)',
                  },
                }}
              />
            );
          })}
        </Box>

        {/* 已選擇提示 */}
        {selectedBodyPart && (
          <Box sx={{ mt: 3, textAlign: 'center' }}>
            <Chip
              label={`已選擇：${selectedBodyPart}`}
              color="primary"
              size="medium"
              sx={{
                fontSize: '15px',
                fontWeight: 600,
                px: 2,
                py: 2.5,
              }}
              onDelete={() => onBodyPartClick('')}
            />
          </Box>
        )}
      </Paper>

      {/* 說明文字 */}
      <Typography
        variant="body2"
        color="text.secondary"
        textAlign="center"
        sx={{ mt: 2, maxWidth: '500px' }}
      >
        💡 提示：點擊圖片上的器官名稱即可選擇受傷部位
      </Typography>
    </Box>
  );
};

export default BodyDiagram;
