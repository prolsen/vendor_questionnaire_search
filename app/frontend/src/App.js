import React, { useState } from 'react';
import { BrowserRouter as Router, Route, Routes, useLocation, Link } from 'react-router-dom';
import SearchPage from './components/SearchPage';
import QuestionPage from './components/QuestionPage';
import UpdatePage from './components/UpdatePage';
import DiffPage from './components/DiffPage';
import { Container, Typography, Tabs, Tab, Box } from '@material-ui/core';

// Separate component for the navigation tabs
function NavigationTabs() {
  const location = useLocation();
  
  return (
    <Box mb={3}>
      <Tabs 
        value={location.pathname}
        indicatorColor="primary"
        textColor="primary"
      >
        <Tab 
          label="Search Questions" 
          value="/" 
          component={Link} 
          to="/"
        />
        <Tab 
          label="Ask Questions" 
          value="/ask" 
          component={Link} 
          to="/ask"
        />
      </Tabs>
    </Box>
  );
}

// Main app content wrapped in router context
function AppContent() {
  const [state, setState] = useState({
    page: 'search',
    updateNodeId: null,
    updateQuestion: "",
    updateAnswer: "",
    originalAnswer: "",
    suggestedAnswer: "",
    diffOriginal: "",
    diffUpdated: ""
  });

  return (
    <Container>
      <Typography variant="h3" component="h1" gutterBottom>
        Vendor Questionnaire Search
      </Typography>
      
      <NavigationTabs />

      <Routes>
        <Route path="/" element={<SearchPage state={state} setState={setState} />} />
        <Route path="/ask" element={<QuestionPage />} />
        <Route path="/update" element={<UpdatePage state={state} setState={setState} />} />
        <Route path="/diff" element={<DiffPage state={state} setState={setState} />} />
      </Routes>
      
      <footer style={{ marginTop: '2rem', paddingBottom: '1rem' }}>
        <Typography variant="body2" color="textSecondary" align="center">
          Vendor Questionnaire Search App - v0.1
        </Typography>
      </footer>
    </Container>
  );
}

// Main App component
function App() {
  return (
    <Router>
      <AppContent />
    </Router>
  );
}

export default App;