import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { TextField, Button, Typography } from '@material-ui/core';

function UpdatePage({ state, setState }) {
  const [updatedAnswer, setUpdatedAnswer] = useState(state.updateAnswer);
  const navigate = useNavigate();

  const handleSave = async () => {
    try {
      const response = await axios.post('http://localhost:8000/update', {
        node_id: state.updateNodeId,
        answer: updatedAnswer
      });
      if (response.status === 200) {
        setState({ ...state, page: 'diff', diffOriginal: state.originalAnswer, diffUpdated: updatedAnswer });
        navigate('/diff');
      }
    } catch (error) {
      console.error('Error updating the answer:', error);
    }
  };

  const handleCancel = () => {
    setState({ ...state, page: 'search' });
    navigate('/');
  };

  const useSuggestedAnswer = () => {
    setUpdatedAnswer(state.suggestedAnswer);
  };

  const toSentenceCase = (text) => {
    return text.charAt(0) + text.slice(1);
  };

  return (
    <div>
      <Typography variant="h5">Vendor questionnaire search</Typography>
      <Typography variant="h6">Update answer for document {state.updateNodeId}</Typography>
      <Typography variant="h6" style={{ marginTop: '20px' }}>Question:</Typography>
      <Typography>{toSentenceCase(state.updateQuestion)}</Typography>
      {state.suggestedAnswer && (
        <>
          <Typography variant="h6" style={{ marginTop: '20px' }}>Suggested improved answer:</Typography>
          <Typography color="primary">{state.suggestedAnswer}</Typography>
          <Button 
            variant="outlined" 
            color="primary" 
            onClick={useSuggestedAnswer}
            style={{ marginTop: '10px', marginBottom: '20px' }}
          >
            USE SUGGESTED ANSWER
          </Button>
        </>
      )}
      <Typography variant="h6" style={{ marginTop: '20px' }}>Current answer:</Typography>
      <TextField
        fullWidth
        multiline
        rows={4}
        variant="outlined"
        label="Edit Answer"
        value={updatedAnswer}
        onChange={(e) => setUpdatedAnswer(e.target.value)}
      />
      <Button variant="contained" color="primary" onClick={handleSave} style={{ marginTop: '10px', marginRight: '10px' }}>Save Updates</Button>
      <Button variant="contained" onClick={handleCancel} style={{ marginTop: '10px' }}>Cancel</Button>
    </div>
  );
}

export default UpdatePage;