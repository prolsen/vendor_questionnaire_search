import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Typography, Button, Box, Paper } from '@material-ui/core';
import { diffLines, formatLines } from 'unidiff';

function DiffPage({ state, setState }) {
  const navigate = useNavigate();

  const diff = diffLines(state.diffOriginal, state.diffUpdated);
  const formattedDiff = formatLines(diff, { context: 3 });

  const handleHome = () => {
    setState({ ...state, page: 'search' });
    navigate('/');
  };

  return (
    <Box p={3}>
      <Typography variant="h4" gutterBottom>Answer Changes</Typography>
      
      <Box my={4}>
        <Typography variant="h5" gutterBottom>Original Answer:</Typography>
        <Paper elevation={3}>
          <Box p={2} overflow="auto">
            <pre style={{ margin: 0, whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>
              {state.diffOriginal}
            </pre>
          </Box>
        </Paper>
      </Box>
      
      <Box my={4}>
        <Typography variant="h5" gutterBottom>Updated Answer:</Typography>
        <Paper elevation={3}>
          <Box p={2} overflow="auto">
            <pre style={{ margin: 0, whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>
              {state.diffUpdated}
            </pre>
          </Box>
        </Paper>
      </Box>
      
      <Box my={4}>
        <Typography variant="h5" gutterBottom>Difference:</Typography>
        <Paper elevation={3}>
          <Box p={2} overflow="auto">
            <pre style={{ margin: 0, whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>
              {formattedDiff}
            </pre>
          </Box>
        </Paper>
      </Box>
      
      <Box mt={4}>
        <Button variant="contained" color="primary" onClick={handleHome}>
          Home
        </Button>
      </Box>
    </Box>
  );
}

export default DiffPage;