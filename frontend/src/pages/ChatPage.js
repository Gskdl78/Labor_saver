import React, { useState, useRef, useEffect } from 'react';
import {
  Box,
  Container,
  Paper,
  Typography,
  TextField,
  IconButton,
  List,
  ListItem,
  Avatar,
  Chip,
  CircularProgress,
  Alert,
} from '@mui/material';
import {
  Send,
  Person,
  SmartToy,
  Clear,
} from '@mui/icons-material';
import { chatAPI } from '../services/api';

const ChatPage = () => {
  const [messages, setMessages] = useState([
    {
      id: 1,
      type: 'bot',
      content: '您好！我是智慧勞災保險諮詢助手。我可以幫助您了解勞災保險的相關規定、申請流程和給付標準。請問您有什麼問題嗎？',
      timestamp: new Date(),
    }
  ]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  // 預設問題 - 從後端API獲取
  const [suggestedQuestions, setSuggestedQuestions] = useState([
    '如何申請失能給付？',
    '失能等級如何評估？',
    '什麼是職業傷病？',
    '勞工保險的保障範圍有哪些？',
    '失能給付金額如何計算？',
  ]);

  // 自動滾動到最新訊息
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // 載入常見問題列表
  useEffect(() => {
    const loadPresetQuestions = async () => {
      try {
        const response = await fetch('http://127.0.0.1:8000/api/chat/preset-questions');
        const data = await response.json();
        if (data.questions && data.questions.length > 0) {
          setSuggestedQuestions(data.questions.slice(0, 10)); // 只顯示前10個問題
        }
      } catch (error) {
        console.error('載入常見問題失敗:', error);
        // 保持預設問題
      }
    };
    
    loadPresetQuestions();
  }, []);

  // 發送訊息
  const handleSendMessage = async (messageText = inputMessage) => {
    if (!messageText.trim()) return;

    const userMessage = {
      id: Date.now(),
      type: 'user',
      content: messageText.trim(),
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setIsLoading(true);
    setError(null);

    try {
      console.log('發送訊息:', messageText.trim());
      const response = await chatAPI.sendMessage(messageText.trim());
      console.log('收到響應:', response);
      
      const botMessage = {
        id: Date.now() + 1,
        type: 'bot',
        content: response.data.response,
        timestamp: new Date(),
        sources: response.data.sources || [],
      };

      setMessages(prev => [...prev, botMessage]);
    } catch (err) {
      console.error('發送訊息失敗:', err);
      console.error('錯誤詳情:', err.response?.data);
      console.error('錯誤狀態:', err.response?.status);
      
      let errorMsg = '抱歉，處理您的問題時發生錯誤，請稍後再試。';
      
      if (err.code === 'ECONNREFUSED') {
        errorMsg = '無法連接到後端服務，請確認後端是否正在運行。';
      } else if (err.response?.status === 404) {
        errorMsg = 'API端點不存在，請檢查後端配置。';
      } else if (err.response?.status >= 500) {
        errorMsg = '後端服務器錯誤，請稍後再試。';
      }
      
      setError(errorMsg);
      
      const errorMessage = {
        id: Date.now() + 1,
        type: 'bot',
        content: errorMsg,
        timestamp: new Date(),
        isError: true,
      };

      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  // 處理輸入框按鍵
  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  // 清除對話
  const handleClearChat = () => {
    setMessages([
      {
        id: 1,
        type: 'bot',
        content: '對話已清除。請問您有什麼問題嗎？',
        timestamp: new Date(),
      }
    ]);
    setError(null);
  };

  // 格式化時間
  const formatTime = (date) => {
    return date.toLocaleTimeString('zh-TW', {
      hour: '2-digit',
      minute: '2-digit',
    });
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
        語言模型諮商
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {/* 主要內容區域 */}
      <Box sx={{ display: 'flex', gap: 3 }}>
        {/* 聊天視窗 */}
        <Paper
          elevation={3}
          sx={{
            flex: 1,
            height: '600px',
            display: 'flex',
            flexDirection: 'column',
            overflow: 'hidden',
          }}
        >
        {/* 聊天標題列 */}
        <Box
          sx={{
            p: 2,
            bgcolor: 'primary.main',
            color: 'white',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
          }}
        >
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <SmartToy />
            <Typography variant="h6">智慧勞災諮詢助手</Typography>
          </Box>
          <IconButton
            color="inherit"
            onClick={handleClearChat}
            title="清除對話"
          >
            <Clear />
          </IconButton>
        </Box>

        {/* 訊息列表 */}
        <Box
          sx={{
            flex: 1,
            overflow: 'auto',
            p: 1,
            bgcolor: '#f5f5f5',
          }}
        >
          <List sx={{ py: 0 }}>
            {messages.map((message) => (
              <ListItem
                key={message.id}
                sx={{
                  display: 'flex',
                  flexDirection: message.type === 'user' ? 'row-reverse' : 'row',
                  alignItems: 'flex-start',
                  mb: 2,
                }}
              >
                <Avatar
                  sx={{
                    bgcolor: message.type === 'user' ? 'primary.main' : 'secondary.main',
                    mx: 1,
                  }}
                >
                  {message.type === 'user' ? <Person /> : <SmartToy />}
                </Avatar>
                <Box
                  sx={{
                    maxWidth: '70%',
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: message.type === 'user' ? 'flex-end' : 'flex-start',
                  }}
                >
                  <Paper
                    elevation={1}
                    sx={{
                      p: 2,
                      bgcolor: message.type === 'user' ? 'primary.main' : 'white',
                      color: message.type === 'user' ? 'white' : 'text.primary',
                      borderRadius: message.type === 'user' ? '18px 18px 4px 18px' : '18px 18px 18px 4px',
                      border: message.isError ? '1px solid #f44336' : 'none',
                    }}
                  >
                    <Typography
                      variant="body1"
                      sx={{
                        whiteSpace: 'pre-wrap',
                        wordBreak: 'break-word',
                      }}
                    >
                      {message.content}
                    </Typography>
                    {message.sources && message.sources.length > 0 && (
                      <Box sx={{ mt: 1 }}>
                        <Typography variant="caption" color="text.secondary">
                          參考資料：
                        </Typography>
                        {message.sources.slice(0, 3).map((source, index) => (
                          <Chip
                            key={index}
                            label={source.metadata?.type || '相關條文'}
                            size="small"
                            sx={{ ml: 0.5, mt: 0.5 }}
                          />
                        ))}
                      </Box>
                    )}
                  </Paper>
                  <Typography
                    variant="caption"
                    color="text.secondary"
                    sx={{ mt: 0.5, px: 1 }}
                  >
                    {formatTime(message.timestamp)}
                  </Typography>
                </Box>
              </ListItem>
            ))}
            {isLoading && (
              <ListItem>
                <Avatar sx={{ bgcolor: 'secondary.main', mx: 1 }}>
                  <SmartToy />
                </Avatar>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <CircularProgress size={20} />
                  <Typography variant="body2" color="text.secondary">
                    正在思考中...
                  </Typography>
                </Box>
              </ListItem>
            )}
          </List>
          <div ref={messagesEndRef} />
        </Box>

        {/* 輸入區域 */}
        <Box sx={{ p: 2, bgcolor: 'white', borderTop: '1px solid #e0e0e0' }}>
          <Box sx={{ display: 'flex', gap: 1, alignItems: 'flex-end' }}>
            <TextField
              ref={inputRef}
              fullWidth
              multiline
              maxRows={3}
              variant="outlined"
              placeholder="請輸入您的問題..."
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              onKeyPress={handleKeyPress}
              disabled={isLoading}
              sx={{
                '& .MuiOutlinedInput-root': {
                  borderRadius: '20px',
                },
              }}
            />
            <IconButton
              color="primary"
              onClick={() => handleSendMessage()}
              disabled={!inputMessage.trim() || isLoading}
              sx={{
                bgcolor: 'primary.main',
                color: 'white',
                '&:hover': {
                  bgcolor: 'primary.dark',
                },
                '&.Mui-disabled': {
                  bgcolor: 'grey.300',
                },
              }}
            >
              <Send />
            </IconButton>
          </Box>
        </Box>
        </Paper>

        {/* 常見問題側邊欄 */}
        <Paper
          elevation={2}
          sx={{
            width: '300px',
            height: '600px',
            display: 'flex',
            flexDirection: 'column',
            overflow: 'hidden',
          }}
        >
          <Box
            sx={{
              p: 2,
              bgcolor: 'secondary.main',
              color: 'white',
              textAlign: 'center',
            }}
          >
            <Typography variant="h6">常見問題</Typography>
          </Box>
          
          <Box
            sx={{
              flex: 1,
              overflow: 'auto',
              p: 2,
            }}
          >
            <List sx={{ py: 0 }}>
              {suggestedQuestions.map((question, index) => (
                <ListItem
                  key={index}
                  sx={{
                    p: 1,
                    mb: 1,
                    borderRadius: 2,
                    bgcolor: 'grey.50',
                    cursor: 'pointer',
                    '&:hover': {
                      bgcolor: 'primary.light',
                      color: 'white',
                    },
                    transition: 'all 0.2s ease-in-out',
                  }}
                  onClick={() => handleSendMessage(question)}
                >
                  <Typography
                    variant="body2"
                    sx={{
                      textAlign: 'center',
                      fontWeight: 500,
                      lineHeight: 1.4,
                    }}
                  >
                    {question}
                  </Typography>
                </ListItem>
              ))}
            </List>
          </Box>
        </Paper>
      </Box>
    </Container>
  );
};

export default ChatPage;
