import React from 'react';
import { Box, Typography } from '@mui/material';

const BodyDiagram = ({ selectedBodyPart, onBodyPartClick }) => {
  // 身體部位樣式
  const getPartStyle = (partName) => ({
    cursor: 'pointer',
    transition: 'all 0.15s ease',
    filter: selectedBodyPart === partName 
      ? 'drop-shadow(0 4px 8px rgba(102, 126, 234, 0.5))' 
      : 'none',
    '&:hover': {
      filter: 'drop-shadow(0 2px 4px rgba(0, 0, 0, 0.3))',
    },
  });

  const handlePartClick = (partName) => {
    if (onBodyPartClick) {
      onBodyPartClick(partName);
    }
  };

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
      <Typography variant="h6" gutterBottom sx={{ mb: 2 }}>
        可點擊的人體部位圖
      </Typography>
      
      <Box
        sx={{
          maxWidth: '400px',
          width: '100%',
          '& svg': {
            width: '100%',
            height: 'auto',
            display: 'block',
          },
        }}
      >
        <svg viewBox="0 0 360 740" role="img" aria-label="人體可點擊圖">
          <defs>
            <style>
              {`
                :root {
                  --skin: #F4C7A7;
                  --top: #3BA7F0;
                  --bottom: #FF826E;
                  --hover: rgba(102, 126, 234, 0.3);
                }
                .hit { fill: transparent; pointer-events: all; }
                .part { transition: filter 0.15s ease; }
                .part:hover { filter: drop-shadow(0 2px 4px var(--hover)); }
                .selected { filter: drop-shadow(0 4px 8px rgba(102, 126, 234, 0.5)); }
              `}
            </style>
          </defs>
          
          <g>
            {/* 地面陰影 */}
            <ellipse cx="180" cy="720" rx="70" ry="16" fill="#000" opacity="0.06"/>

            {/* 頭部 */}
            <g onClick={() => handlePartClick('頭')}>
              <rect className="hit" x="120" y="80" width="120" height="140"/>
              <g className={`part ${selectedBodyPart === '頭' ? 'selected' : ''}`}>
                <ellipse cx="180" cy="150" rx="55" ry="70" fill="var(--skin)"/>
              </g>
            </g>

            {/* 頸部 */}
            <g onClick={() => handlePartClick('頸部')}>
              <rect className="hit" x="158" y="212" width="44" height="24"/>
              <g className={`part ${selectedBodyPart === '頸部' ? 'selected' : ''}`}>
                <rect x="158" y="212" width="44" height="24" rx="8" fill="var(--skin)"/>
              </g>
            </g>

            {/* 身體 */}
            <g onClick={() => handlePartClick('身體')}>
              <rect className="hit" x="110" y="236" width="140" height="160"/>
              <g className={`part ${selectedBodyPart === '身體' ? 'selected' : ''}`}>
                <rect x="110" y="236" width="140" height="160" rx="16" fill="var(--top)"/>
              </g>
            </g>

            {/* 左臂 */}
            <g onClick={() => handlePartClick('左臂')}>
              <rect className="hit" x="44" y="256" width="70" height="214"/>
              <g className={`part ${selectedBodyPart === '左臂' ? 'selected' : ''}`}>
                <rect x="66" y="256" width="28" height="204" rx="14" fill="var(--skin)"/>
              </g>
            </g>

            {/* 右臂 */}
            <g onClick={() => handlePartClick('右臂')}>
              <rect className="hit" x="246" y="256" width="70" height="214"/>
              <g className={`part ${selectedBodyPart === '右臂' ? 'selected' : ''}`}>
                <rect x="266" y="256" width="28" height="204" rx="14" fill="var(--skin)"/>
              </g>
            </g>

            {/* 腰部/骨盆 */}
            <g onClick={() => handlePartClick('腰部')}>
              <rect className="hit" x="120" y="396" width="120" height="72"/>
              <g className={`part ${selectedBodyPart === '腰部' ? 'selected' : ''}`}>
                <rect x="120" y="396" width="120" height="72" rx="14" fill="var(--bottom)"/>
              </g>
            </g>

            {/* 左腿 */}
            <g onClick={() => handlePartClick('左腿')}>
              <rect className="hit" x="130" y="468" width="40" height="150"/>
              <g className={`part ${selectedBodyPart === '左腿' ? 'selected' : ''}`}>
                <rect x="130" y="468" width="40" height="150" rx="18" fill="var(--skin)"/>
              </g>
            </g>

            {/* 右腿 */}
            <g onClick={() => handlePartClick('右腿')}>
              <rect className="hit" x="190" y="468" width="40" height="150"/>
              <g className={`part ${selectedBodyPart === '右腿' ? 'selected' : ''}`}>
                <rect x="190" y="468" width="40" height="150" rx="18" fill="var(--skin)"/>
              </g>
            </g>

            {/* 左腳 */}
            <g onClick={() => handlePartClick('左腳')}>
              <rect className="hit" x="126" y="618" width="48" height="34"/>
              <g className={`part ${selectedBodyPart === '左腳' ? 'selected' : ''}`}>
                <rect x="126" y="618" width="48" height="28" rx="10" fill="var(--skin)"/>
              </g>
            </g>

            {/* 右腳 */}
            <g onClick={() => handlePartClick('右腳')}>
              <rect className="hit" x="186" y="618" width="48" height="34"/>
              <g className={`part ${selectedBodyPart === '右腳' ? 'selected' : ''}`}>
                <rect x="186" y="618" width="48" height="28" rx="10" fill="var(--skin)"/>
              </g>
            </g>
          </g>
        </svg>
      </Box>

      <Typography 
        variant="body2" 
        color="text.secondary" 
        textAlign="center"
        sx={{ mt: 2, maxWidth: '300px' }}
      >
        點擊身體部位以選擇受傷位置，選中的部位會有藍色陰影顯示
      </Typography>
    </Box>
  );
};

export default BodyDiagram;
