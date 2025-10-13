import React from 'react';
import {
  Box,
  Container,
  Typography,
  Grid,
  Card,
  CardContent,
  CardMedia,
  Button,
  Paper,
} from '@mui/material';
import {
  Chat,
  Map,
  TouchApp,
  Security,
  Speed,
  Support,
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import ImageCarousel from '../components/ImageCarousel';

const HomePage = () => {
  const navigate = useNavigate();

  const features = [
    {
      icon: <Chat sx={{ fontSize: 40, color: '#667eea' }} />,
      title: '職護喵',
      description: '透過AI智能諮詢，快速了解勞災保險相關規定與申請流程',
      path: '/chat',
    },
    {
      icon: <Map sx={{ fontSize: 40, color: '#667eea' }} />,
      title: '地圖搜索',
      description: '找到最近的合格醫院、復健中心或勞工服務中心',
      path: '/map',
    },
    {
      icon: <TouchApp sx={{ fontSize: 40, color: '#667eea' }} />,
      title: '點身健檢',
      description: '點擊受傷部位，快速查詢失能等級與給付標準',
      path: '/body-interaction',
    },
  ];

  const advantages = [
    {
      icon: <Security sx={{ fontSize: 30, color: '#764ba2' }} />,
      title: '專業可靠',
      description: '基於官方勞保資料集，確保資訊準確性',
    },
    {
      icon: <Speed sx={{ fontSize: 30, color: '#764ba2' }} />,
      title: '快速便捷',
      description: '一站式服務，快速獲得所需資訊',
    },
    {
      icon: <Support sx={{ fontSize: 30, color: '#764ba2' }} />,
      title: '全天候服務',
      description: '24小時線上諮詢，隨時為您服務',
    },
  ];

  return (
    <Box>
      {/* Hero Section */}
      <Box
        sx={{
          background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
          color: 'white',
          py: 8,
          position: 'relative',
          overflow: 'hidden',
        }}
      >
        <Container maxWidth="lg">
          <Grid container spacing={4} alignItems="center">
            <Grid item xs={12} md={6}>
              <Typography
                variant="h2"
                component="h1"
                gutterBottom
                sx={{ fontWeight: 700, mb: 2 }}
              >
                勞資屬道山
              </Typography>
              <Typography
                variant="h5"
                sx={{ mb: 4, opacity: 0.9, fontWeight: 400 }}
              >
                提供專業的勞災保險諮詢、地圖搜索和失能給付查詢服務
              </Typography>
              <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
                <Button
                  variant="contained"
                  size="large"
                  onClick={() => navigate('/chat')}
                  sx={{
                    bgcolor: 'white',
                    color: '#667eea',
                    '&:hover': {
                      bgcolor: 'rgba(255, 255, 255, 0.9)',
                    },
                  }}
                >
                  開始諮詢
                </Button>
                <Button
                  variant="outlined"
                  size="large"
                  onClick={() => navigate('/body-interaction')}
                  sx={{
                    borderColor: 'white',
                    color: 'white',
                    '&:hover': {
                      borderColor: 'white',
                      bgcolor: 'rgba(255, 255, 255, 0.1)',
                    },
                  }}
                >
                  失能查詢
                </Button>
              </Box>
            </Grid>
            <Grid item xs={12} md={6}>
              <ImageCarousel />
            </Grid>
          </Grid>
        </Container>
      </Box>

      {/* Features Section */}
      <Container maxWidth="lg" sx={{ py: 8 }}>
        <Typography
          variant="h3"
          component="h2"
          textAlign="center"
          gutterBottom
          sx={{ mb: 6, fontWeight: 600 }}
        >
          主要功能
        </Typography>
        <Grid container spacing={4}>
          {features.map((feature, index) => (
            <Grid item xs={12} md={4} key={index}>
              <Card
                sx={{
                  height: '100%',
                  cursor: 'pointer',
                  transition: 'all 0.3s ease',
                  '&:hover': {
                    transform: 'translateY(-8px)',
                    boxShadow: 4,
                  },
                }}
                onClick={() => navigate(feature.path)}
              >
                <CardContent sx={{ textAlign: 'center', p: 4 }}>
                  <Box sx={{ mb: 2 }}>
                    {feature.icon}
                  </Box>
                  <Typography
                    variant="h5"
                    component="h3"
                    gutterBottom
                    sx={{ fontWeight: 600 }}
                  >
                    {feature.title}
                  </Typography>
                  <Typography
                    variant="body1"
                    color="text.secondary"
                    sx={{ mb: 3 }}
                  >
                    {feature.description}
                  </Typography>
                  <Button
                    variant="outlined"
                    color="primary"
                    onClick={(e) => {
                      e.stopPropagation();
                      navigate(feature.path);
                    }}
                  >
                    了解更多
                  </Button>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      </Container>

      {/* About Section */}
      <Box sx={{ bgcolor: '#f8f9fa', py: 8 }}>
        <Container maxWidth="lg">
          <Typography
            variant="h3"
            component="h2"
            textAlign="center"
            gutterBottom
            sx={{ mb: 6, fontWeight: 600 }}
          >
            為什麼選擇我們
          </Typography>
          <Grid container spacing={4}>
            {advantages.map((advantage, index) => (
              <Grid item xs={12} md={4} key={index}>
                <Paper
                  sx={{
                    p: 4,
                    textAlign: 'center',
                    height: '100%',
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                  }}
                >
                  <Box sx={{ mb: 2 }}>
                    {advantage.icon}
                  </Box>
                  <Typography
                    variant="h6"
                    component="h3"
                    gutterBottom
                    sx={{ fontWeight: 600 }}
                  >
                    {advantage.title}
                  </Typography>
                  <Typography
                    variant="body1"
                    color="text.secondary"
                  >
                    {advantage.description}
                  </Typography>
                </Paper>
              </Grid>
            ))}
          </Grid>
        </Container>
      </Box>

      {/* CTA Section */}
      <Box
        sx={{
          background: 'linear-gradient(135deg, #764ba2 0%, #667eea 100%)',
          color: 'white',
          py: 8,
        }}
      >
        <Container maxWidth="md" sx={{ textAlign: 'center' }}>
          <Typography
            variant="h4"
            component="h2"
            gutterBottom
            sx={{ fontWeight: 600, mb: 2 }}
          >
            立即開始使用
          </Typography>
          <Typography
            variant="h6"
            sx={{ mb: 4, opacity: 0.9 }}
          >
            讓我們幫助您快速了解勞災保險相關資訊
          </Typography>
          <Box sx={{ display: 'flex', gap: 2, justifyContent: 'center', flexWrap: 'wrap' }}>
            <Button
              variant="contained"
              size="large"
              onClick={() => navigate('/chat')}
              sx={{
                bgcolor: 'white',
                color: '#764ba2',
                '&:hover': {
                  bgcolor: 'rgba(255, 255, 255, 0.9)',
                },
              }}
            >
              開始諮詢
            </Button>
            <Button
              variant="outlined"
              size="large"
              onClick={() => navigate('/map')}
              sx={{
                borderColor: 'white',
                color: 'white',
                '&:hover': {
                  borderColor: 'white',
                  bgcolor: 'rgba(255, 255, 255, 0.1)',
                },
              }}
            >
              尋找服務據點
            </Button>
          </Box>
        </Container>
      </Box>
    </Box>
  );
};

export default HomePage;
