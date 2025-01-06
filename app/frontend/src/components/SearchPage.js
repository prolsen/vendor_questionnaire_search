import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { TextField, Button, Typography, CircularProgress, Accordion, AccordionSummary, AccordionDetails, Box, Snackbar, Select, MenuItem, FormControl, InputLabel } from '@material-ui/core';
import ExpandMoreIcon from '@material-ui/icons/ExpandMore';
import FileCopyIcon from '@material-ui/icons/FileCopy';

function SearchPage({ state, setState }) {
  const [query, setQuery] = useState('');
  const [product, setProduct] = useState('All');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [snackbarOpen, setSnackbarOpen] = useState(false);
  const navigate = useNavigate();

  const handleSearch = async () => {
    setLoading(true);
    try {
      const response = await axios.post('http://localhost:8000/query', {
        query: query,
        product: product
      });
      setResult(response.data);
    } catch (error) {
      console.error('Error querying the RAG bot:', error);
    }
    setLoading(false);
  };

  const handleUpdate = (nodeId, question, answer, suggestedAnswer) => {
    setState({
      ...state,
      page: 'update',
      updateNodeId: nodeId,
      updateQuestion: question,
      updateAnswer: answer,
      originalAnswer: answer,
      suggestedAnswer
    });
    navigate('/update');
  };

  const toSentenceCase = (str) => {
    return str.charAt(0) + str.slice(1);
  };

  const getHighestScoredAnswer = (sourceNodes) => {
    if (!sourceNodes || sourceNodes.length === 0) return 'No answer available';
    const highestScoredNode = sourceNodes.reduce((prev, current) => 
      (prev.score > current.score) ? prev : current
    );
    return highestScoredNode.answer;
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
      <Typography variant="h5">Search</Typography>
      <TextField
        fullWidth
        variant="outlined"
        label="Enter your query"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
      />

      <Box mt={2} display="flex" alignItems="center">
        <FormControl variant="outlined" style={{ minWidth: 120, marginRight: 16 }}>
          <InputLabel>Product</InputLabel>
          <Select
            value={product}
            onChange={(e) => setProduct(e.target.value)}
            label="Filter by Product"
          >
            <MenuItem value="All">All</MenuItem>
            <MenuItem value="Product1">Product1</MenuItem>
            <MenuItem value="Product2">Product2</MenuItem>
          </Select>
        </FormControl>
        <Button variant="contained" color="primary" onClick={handleSearch} disabled={loading}>
          {loading ? <CircularProgress size={24} /> : 'Search'}
        </Button>
      </Box>
      {result && (
        <Box mt={4}>
          <Typography variant="h6">Answer</Typography>
          <Typography variant="body2" color="textSecondary" paragraph>
            The initial answer is taken from the highest similarity question within the source documents listed below.
          </Typography>
          <Box display="flex" alignItems="center">
            <Typography>{toSentenceCase(getHighestScoredAnswer(result.source_nodes))}</Typography>
            <Button
              startIcon={<FileCopyIcon />}
              onClick={() => copyToClipboard(toSentenceCase(getHighestScoredAnswer(result.source_nodes)))}
            >
              Copy
            </Button>
          </Box>
          
          {result.suggested_answer && (
            <Box mt={3}>
              <Typography variant="h6">Suggested Improved Answer</Typography>
              <Typography variant="body2" color="textSecondary" paragraph>
                The suggested improved answer below is an AI's attempt at enhancing the initial answer above.
              </Typography>
              <Box display="flex" alignItems="center">
                <Typography color="primary">{result.suggested_answer}</Typography>
                <Button
                  startIcon={<FileCopyIcon />}
                  onClick={() => copyToClipboard(result.suggested_answer)}
                >
                  Copy
                </Button>
              </Box>
            </Box>
          )}
          
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

                    <Button
                      variant="outlined"
                      color="primary"
                      onClick={() => handleUpdate(node.node_id, node.question, node.answer, result.suggested_answer)}
                    >
                      Update
                    </Button>
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

export default SearchPage;