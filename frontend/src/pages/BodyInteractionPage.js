import React, { useState } from 'react';
import {
  Box,
  Container,
  Typography,
  Paper,
  Grid,
  TextField,
  Button,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Card,
  CardContent,
  List,
  ListItem,
  ListItemText,
  Chip,
  Alert,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  CircularProgress,
} from '@mui/material';
import {
  ExpandMore,
  Search,
  TouchApp,
} from '@mui/icons-material';
import { disabilityAPI } from '../services/api';
import BodyDiagram from '../components/BodyDiagram';

const BodyInteractionPage = () => {
  const [selectedBodyPart, setSelectedBodyPart] = useState('');
  const [injuryDescription, setInjuryDescription] = useState('');
  const [disabilityLevel, setDisabilityLevel] = useState('');
  const [analysisResult, setAnalysisResult] = useState(null);
  const [benefitResult, setBenefitResult] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [disabilityLevels] = useState([
    '1', '2', '3', '4', '5', '6', '7', '8', '9', '10',
    '11', '12', '13', '14', '15'
  ]);

  // 處理身體部位點擊
  const handleBodyPartClick = (bodyPart) => {
    setSelectedBodyPart(bodyPart);
    setError(null);
  };

  // 分析身體部位傷害
  const handleAnalyzeInjury = async () => {
    if (!selectedBodyPart || !injuryDescription.trim()) {
      setError('請選擇受傷部位並描述傷害情況');
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      console.log('發送分析請求:', { selectedBodyPart, injuryDescription });
      const response = await disabilityAPI.analyzeBodyPartInjury(
        selectedBodyPart,
        injuryDescription
      );
      console.log('收到分析響應:', response.data);
      setAnalysisResult(response.data);
    } catch (err) {
      console.error('分析失敗:', err);
      console.error('錯誤詳情:', err.response?.data);
      setError('分析身體部位傷害時發生錯誤');
    } finally {
      setIsLoading(false);
    }
  };

  // 查詢失能給付
  const handleQueryBenefit = async () => {
    if (!disabilityLevel) {
      setError('請選擇失能等級');
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const response = await disabilityAPI.getDisabilityBenefit(disabilityLevel);
      setBenefitResult(response.data);
    } catch (err) {
      console.error('查詢給付失敗:', err);
      setError('查詢失能給付時發生錯誤');
    } finally {
      setIsLoading(false);
    }
  };

  // 清除結果
  const handleClearResults = () => {
    setAnalysisResult(null);
    setBenefitResult(null);
    setSelectedBodyPart('');
    setInjuryDescription('');
    setDisabilityLevel('');
    setError(null);
  };

  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      <Typography
        variant="h4"
        component="h1"
        gutterBottom
        textAlign="center"
        sx={{ mb: 4, fontWeight: 600 }}
      >
        點身健檢
      </Typography>

      <Typography
        variant="subtitle1"
        textAlign="center"
        color="text.secondary"
        sx={{ mb: 4 }}
      >
        點擊人體部位圖，描述傷害情況，查詢相關的失能等級與給付標準
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      <Grid container spacing={4}>
        {/* 左側：人體部位圖 */}
        <Grid item xs={12} lg={5}>
          <Paper elevation={3} sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              點擊受傷部位
            </Typography>
            <BodyDiagram
              selectedBodyPart={selectedBodyPart}
              onBodyPartClick={handleBodyPartClick}
            />
            {selectedBodyPart && (
              <Box sx={{ mt: 2, textAlign: 'center' }}>
                <Chip
                  label={`已選擇：${selectedBodyPart}`}
                  color="primary"
                  icon={<TouchApp />}
                />
              </Box>
            )}
          </Paper>
        </Grid>

        {/* 右側：輸入和結果區域 */}
        <Grid item xs={12} lg={7}>
          <Grid container spacing={3}>
            {/* 傷害分析區域 */}
            <Grid item xs={12}>
              <Paper elevation={3} sx={{ p: 3 }}>
                <Typography variant="h6" gutterBottom>
                  傷害情況分析
                </Typography>
                
                <Box sx={{ mb: 2 }}>
                  <TextField
                    fullWidth
                    label="受傷部位"
                    value={selectedBodyPart}
                    InputProps={{ readOnly: true }}
                    helperText="請點擊左側人體部位圖選擇"
                  />
                </Box>

                <Box sx={{ mb: 2 }}>
                  <TextField
                    fullWidth
                    multiline
                    rows={3}
                    label="傷害描述"
                    placeholder="請詳細描述受傷情況，例如：骨折、肌肉撕裂、功能障礙等..."
                    value={injuryDescription}
                    onChange={(e) => setInjuryDescription(e.target.value)}
                  />
                </Box>

                <Button
                  variant="contained"
                  onClick={handleAnalyzeInjury}
                  disabled={!selectedBodyPart || !injuryDescription.trim() || isLoading}
                  startIcon={isLoading ? <CircularProgress size={20} /> : <Search />}
                  sx={{ mb: 2 }}
                >
                  {isLoading ? '分析中...' : '分析可能的失能等級'}
                </Button>

                {analysisResult && (
                  <Box sx={{ mt: 2 }}>
                    <Typography variant="subtitle1" gutterBottom>
                      分析結果：
                    </Typography>
                    
                    {analysisResult.analysis ? (
                      <Paper sx={{ p: 2, bgcolor: 'grey.50', mb: 2 }}>
                        <Typography 
                          variant="body1" 
                          sx={{ 
                            whiteSpace: 'pre-line',
                            fontFamily: 'monospace',
                            lineHeight: 1.6
                          }}
                        >
                          {analysisResult.analysis}
                        </Typography>
                      </Paper>
                    ) : analysisResult.possible_disabilities?.length > 0 ? (
                      <Box sx={{ mb: 2 }}>
                        <Typography variant="body2" gutterBottom>
                          可能的失能項目：
                        </Typography>
                        {analysisResult.possible_disabilities.map((disability, index) => (
                          <Accordion key={index} sx={{ mb: 1 }}>
                            <AccordionSummary expandIcon={<ExpandMore />}>
                              <Box>
                                <Typography variant="body1" sx={{ fontWeight: 600 }}>
                                  {disability.type} - 等級 {disability.level}
                                </Typography>
                                <Typography variant="body2" color="text.secondary">
                                  {disability.item}
                                </Typography>
                              </Box>
                            </AccordionSummary>
                            <AccordionDetails>
                              <Typography variant="body2" paragraph>
                                <strong>失能狀態：</strong>{disability.state}
                              </Typography>
                              <Typography variant="body2">
                                <strong>審核基準：</strong>{disability.criteria}
                              </Typography>
                            </AccordionDetails>
                          </Accordion>
                        ))}
                      </Box>
                    ) : (
                      <Alert severity="info" sx={{ mb: 2 }}>
                        未找到與該部位直接相關的失能項目，建議諮詢專業醫師進行評估。
                      </Alert>
                    )}

                    {analysisResult.recommendations?.length > 0 && (
                      <Box>
                        <Typography variant="body2" gutterBottom>
                          建議：
                        </Typography>
                        <List dense>
                          {analysisResult.recommendations.map((recommendation, index) => (
                            <ListItem key={index}>
                              <ListItemText
                                primary={recommendation}
                                sx={{ py: 0 }}
                              />
                            </ListItem>
                          ))}
                        </List>
                      </Box>
                    )}
                  </Box>
                )}
              </Paper>
            </Grid>

            {/* 失能給付查詢區域 */}
            <Grid item xs={12}>
              <Paper elevation={3} sx={{ p: 3 }}>
                <Typography variant="h6" gutterBottom>
                  失能給付查詢
                </Typography>
                
                <Box sx={{ mb: 2 }}>
                  <FormControl fullWidth>
                    <InputLabel>失能等級</InputLabel>
                    <Select
                      value={disabilityLevel}
                      onChange={(e) => setDisabilityLevel(e.target.value)}
                      label="失能等級"
                    >
                      {disabilityLevels.map((level) => (
                        <MenuItem key={level} value={level}>
                          第 {level} 級
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                </Box>

                <Button
                  variant="contained"
                  onClick={handleQueryBenefit}
                  disabled={!disabilityLevel || isLoading}
                  startIcon={isLoading ? <CircularProgress size={20} /> : <Search />}
                  sx={{ mb: 2 }}
                >
                  {isLoading ? '查詢中...' : '查詢給付標準'}
                </Button>

                {benefitResult && (
                  <Card sx={{ mt: 2 }}>
                    <CardContent>
                      <Typography variant="h6" gutterBottom>
                        第 {benefitResult.level} 級失能給付標準
                      </Typography>
                      <Grid container spacing={2}>
                        <Grid item xs={12} sm={6}>
                          <Box sx={{ p: 2, bgcolor: '#e3f2fd', borderRadius: 1 }}>
                            <Typography variant="subtitle2" gutterBottom>
                              普通傷病失能補助費
                            </Typography>
                            <Typography variant="h6" color="primary">
                              {benefitResult.general_benefit}
                            </Typography>
                          </Box>
                        </Grid>
                        <Grid item xs={12} sm={6}>
                          <Box sx={{ p: 2, bgcolor: '#f3e5f5', borderRadius: 1 }}>
                            <Typography variant="subtitle2" gutterBottom>
                              職業傷病失能補償費
                            </Typography>
                            <Typography variant="h6" color="secondary">
                              {benefitResult.occupational_benefit}
                            </Typography>
                          </Box>
                        </Grid>
                      </Grid>
                      <Alert severity="info" sx={{ mt: 2 }}>
                        <Typography variant="body2">
                          <strong>說明：</strong>
                          實際給付金額 = 平均月投保薪資 × 給付日數。
                          職業傷病的給付日數較普通傷病為高。
                        </Typography>
                      </Alert>
                    </CardContent>
                  </Card>
                )}
              </Paper>
            </Grid>

            {/* 清除按鈕 */}
            {(analysisResult || benefitResult) && (
              <Grid item xs={12}>
                <Box sx={{ textAlign: 'center' }}>
                  <Button
                    variant="outlined"
                    onClick={handleClearResults}
                    sx={{ minWidth: 120 }}
                  >
                    清除結果
                  </Button>
                </Box>
              </Grid>
            )}
          </Grid>
        </Grid>
      </Grid>
    </Container>
  );
};

export default BodyInteractionPage;
