import React, { useState } from 'react';
import { TextField, Button, Typography, CircularProgress, Accordion, AccordionSummary, AccordionDetails, Box, Snackbar } from '@material-ui/core';
import ExpandMoreIcon from '@material-ui/icons/ExpandMore';
import FileCopyIcon from '@material-ui/icons/FileCopy';
import axios from 'axios';

function QuestionPage() {
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [snackbarOpen, setSnackbarOpen] = useState(false);

  const handleAsk = async () => {
    setLoading(true);
    try {
      const response = await axios.post('http://localhost:8000/ask', {
        query: query
      });
      setResult(response.data);
    } catch (error) {
      console.error('Error querying the RAG bot:', error);
      setResult(null);  // Clear any previous results
    }
    setLoading(false);
  };

  const toSentenceCase = (str) => {
    return str.charAt(0) + str.slice(1);
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text).then(() => {
      setSnackbarOpen(true);
    }, (err) => {
      console.error('Could not copy text: ', err);
    });
  };

  return (
    <div>
      <Typography variant="h5">Ask a Question</Typography>
      <TextField
        fullWidth
        variant="outlined"
        label="Enter your question here"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
      />
      <Box mt={2} display="flex" alignItems="center">
        <Button variant="contained" color="primary" onClick={handleAsk} disabled={loading}>
          {loading ? <CircularProgress size={24} /> : 'Search'}
        </Button>
      </Box>
      {result && (
        <Box mt={4}>
          <Typography variant="h6">Answer</Typography>
          <Typography variant="body2" color="textSecondary" paragraph>
            The answer is generated based on analyzing all relevant documents in the knowledge base.
          </Typography>
          <Box display="flex" alignItems="center">
            <Typography>{result.answer}</Typography>
            <Button
              startIcon={<FileCopyIcon />}
              onClick={() => copyToClipboard(result.answer)}
            >
              Copy
            </Button>
          </Box>
          
          <Box mt={4}>
            <Typography variant="h6">Source documents</Typography>
            <Typography variant="body2" color="textSecondary" paragraph>
              Source documents are gathered using cosine similarity searches on the search query, 
              which should be the question from the vendor document.
            </Typography>
            {result.source_nodes.map((node, index) => (
              <Accordion key={index}>
                <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                  <Typography>Document {index + 1}: {node.document_name}</Typography>
                </AccordionSummary>
                <AccordionDetails>
                  <Box>
                    <Typography><strong>Question:</strong></Typography>
                    <Typography paragraph>{toSentenceCase(node.question)}</Typography>

                    <Typography><strong>Answer:</strong></Typography>
                    <Typography paragraph>{toSentenceCase(node.answer)}</Typography>
                    
                    <Typography paragraph><strong>Product:</strong> {node.product}</Typography>

                    <Typography paragraph><strong>Score:</strong> {node.score}</Typography>

                    <Typography paragraph><strong>Node ID:</strong> {node.node_id}</Typography>
                  </Box>
                </AccordionDetails>
              </Accordion>
            ))}
          </Box>
        </Box>
      )}
      <Snackbar
        anchorOrigin={{
          vertical: 'bottom',
          horizontal: 'left',
        }}
        open={snackbarOpen}
        autoHideDuration={2000}
        onClose={() => setSnackbarOpen(false)}
        message="Copied to clipboard"
      />
    </div>
  );
}

export default QuestionPage;