import React from 'react';
import { ArrowLeft, Save } from 'lucide-react';

export default function ReviewPage({ data, onReset }) {
    // In a full implementation, you would bind these to state to allow editing
    const handleSave = () => {
        alert("Data validated and saved to Database!");
        onReset();
    };

    return (
        <div style={{ padding: '40px', fontFamily: 'system-ui', maxWidth: '1200px', margin: '0 auto' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <h2>Validation Interface</h2>
                <div>
                    <button onClick={onReset} style={{ marginRight: '10px', padding: '8px 16px', cursor: 'pointer' }}>
                        <ArrowLeft size={16} style={{ verticalAlign: 'middle' }} /> Back to Queue
                    </button>
                    <button onClick={handleSave} style={{ padding: '8px 16px', backgroundColor: '#059669', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer' }}>
                        <Save size={16} style={{ verticalAlign: 'middle', marginRight: '5px' }} /> Confirm & Export
                    </button>
                </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 2fr', gap: '20px', marginTop: '20px' }}>
                {/* Left Column: Metadata & Notes */}
                <div>
                    <div style={{ background: '#f3f4f6', padding: '20px', borderRadius: '8px', marginBottom: '20px' }}>
                        <h3>Document Info</h3>
                        <p><strong>Ladle Capacity:</strong> {data.document_info.ladle_capacity || 'Not detected'}</p>
                        
                        <h3 style={{ marginTop: '20px' }}>Pouring Details</h3>
                        <ul>
                            {data.pouring_details.detected_temperatures?.map((temp, i) => (
                                <li key={i}><strong>Temperature:</strong> {temp}</li>
                            ))}
                        </ul>
                    </div>

                    <div style={{ background: '#fef3c7', padding: '20px', borderRadius: '8px' }}>
                        <h3>Handwritten Notes (TrOCR)</h3>
                        {data.raw_notes?.map((note, i) => (
                            <div key={i} style={{ marginBottom: '10px', padding: '10px', background: 'white', borderRadius: '4px' }}>
                                <p style={{ margin: '0 0 5px 0' }}>{note.text}</p>
                                <small style={{ color: '#6b7280' }}>Confidence: {(note.confidence * 100).toFixed(1)}%</small>
                            </div>
                        ))}
                    </div>
                </div>

                {/* Right Column: Dynamic Tables */}
                <div style={{ background: 'white', border: '1px solid #e5e7eb', padding: '20px', borderRadius: '8px' }}>
                    <h3>Extracted Tables</h3>
                    <p style={{ color: '#6b7280', fontSize: '14px' }}>Dynamic rows extracted via PP-StructureV3</p>
                    
                    <pre style={{ 
                        background: '#1f2937', color: '#f3f4f6', padding: '15px', 
                        borderRadius: '6px', overflowX: 'auto', fontSize: '13px' 
                    }}>
                        {JSON.stringify(data.tables, null, 2)}
                    </pre>
                </div>
            </div>
        </div>
    );
}