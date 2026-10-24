import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './App.css';

function App() {
  const [businesses, setBusinesses] = useState([]);
  const [category, setCategory] = useState('');
  const [location, setLocation] = useState('');
  const [newBiz, setNewBiz] = useState({ name: '', category: '', location: '', description: '' });

  const fetchBusinesses = async () => {
    try {
      const res = await axios.get('/api/businesses', { params: { category, location } });
      setBusinesses(res.data);
    } catch (err) {
      console.error('Error fetching businesses:', err);
    }
  };

  useEffect(() => {
    fetchBusinesses();
  }, []);

  const handleCreate = async (e) => {
    e.preventDefault();
    try {
      await axios.post('/api/businesses', newBiz);
      setNewBiz({ name: '', category: '', location: '', description: '' });
      fetchBusinesses();
    } catch (err) {
      console.error('Error creating business:', err);
    }
  };

  return (
    <div className="App">
      <header className="header">
        <h1>🏪 LocalBizHub</h1>
        <p>Small Business Marketplace</p>
      </header>

      <div className="container">
        <section className="card">
          <h2>Filter Businesses</h2>
          <div className="form-group row">
            <input placeholder="Category (e.g. Bakery)" value={category} onChange={(e) => setCategory(e.target.value)} />
            <input placeholder="Location (e.g. Pune)" value={location} onChange={(e) => setLocation(e.target.value)} />
            <button onClick={fetchBusinesses}>Search</button>
          </div>
        </section>

        <section className="card">
          <h2>Register Business</h2>
          <form onSubmit={handleCreate} className="form-group">
            <input placeholder="Business Name" value={newBiz.name} onChange={(e) => setNewBiz({...newBiz, name: e.target.value})} required />
            <input placeholder="Category" value={newBiz.category} onChange={(e) => setNewBiz({...newBiz, category: e.target.value})} required />
            <input placeholder="Location" value={newBiz.location} onChange={(e) => setNewBiz({...newBiz, location: e.target.value})} required />
            <textarea placeholder="Description" value={newBiz.description} onChange={(e) => setNewBiz({...newBiz, description: e.target.value})} />
            <button type="submit">Add Business</button>
          </form>
        </section>

        <section className="card">
          <h2>Marketplace Listings</h2>
          {businesses.length === 0 ? <p>No businesses found.</p> : (
            <div className="grid">
              {businesses.map((b) => (
                <div key={b.id} className="biz-card">
                  <h3>{b.name}</h3>
                  <span className="badge">{b.category}</span>
                  <p>📍 {b.location}</p>
                  <p>{b.description}</p>
                </div>
              ))}
            </div>
          )}
        </section>
      </div>
    </div>
  );
}

export default App;
