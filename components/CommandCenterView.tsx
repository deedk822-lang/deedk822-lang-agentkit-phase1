
import React, { useState, useCallback } from 'react';
import { COMMAND_SCHEMAS } from '../constants';
import { submitCommand } from '../services/mockPcpApi';
import { analyzeComplexTask } from '../services/geminiService';
import { LedgerEntry } from '../types';

type CommandType = keyof typeof COMMAND_SCHEMAS;

const CommandCenterView: React.FC = () => {
    const [selectedCommand, setSelectedCommand] = useState<CommandType>('SCAN_SITE');
    const [params, setParams] = useState<Record<string, string>>({});
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [lastResult, setLastResult] = useState<LedgerEntry | null>(null);

    const [naturalLanguageTask, setNaturalLanguageTask] = useState('');
    const [isAnalyzing, setIsAnalyzing] = useState(false);
    const [analysisError, setAnalysisError] = useState('');

    const handleCommandChange = useCallback((e: React.ChangeEvent<HTMLSelectElement>) => {
        const newCommand = e.target.value as CommandType;
        setSelectedCommand(newCommand);
        setParams({});
    }, []);

    const handleParamChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
        setParams(prev => ({ ...prev, [e.target.name]: e.target.value }));
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setIsSubmitting(true);
        setLastResult(null);
        const commandSchema = COMMAND_SCHEMAS[selectedCommand];
        const result = await submitCommand({
            command_type: selectedCommand,
            params,
            severity: commandSchema.severity,
        });
        setLastResult(result);
        setIsSubmitting(false);
        setParams({});
    };

    const handleAnalyzeTask = async () => {
        if (!naturalLanguageTask) return;
        setIsAnalyzing(true);
        setAnalysisError('');
        try {
            const resultJson = await analyzeComplexTask(naturalLanguageTask);
            const result = JSON.parse(resultJson);
            
            if (result.error || !result.commands || result.commands.length === 0) {
              setAnalysisError(result.reason || result.error || 'Gemini could not determine a valid command. Please be more specific.');
              return;
            }

            const firstCommand = result.commands[0];
            if (COMMAND_SCHEMAS[firstCommand.command_type as CommandType]) {
                setSelectedCommand(firstCommand.command_type as CommandType);
                setParams(firstCommand.params);
            } else {
                 setAnalysisError(`Gemini suggested an unknown command: ${firstCommand.command_type}`);
            }

        } catch (e) {
            console.error(e);
            setAnalysisError('Failed to parse Gemini response. See console for details.');
        } finally {
            setIsAnalyzing(false);
        }
    };
    
    const currentSchema = COMMAND_SCHEMAS[selectedCommand];

    return (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            <div className="bg-pcp-light-dark border border-pcp-border rounded-lg p-6 space-y-6">
                <div>
                    <h2 className="text-xl font-bold text-pcp-text">Manual Command Execution</h2>
                    <p className="text-sm text-pcp-text-dim mt-1">Directly issue a command to the PCP.</p>
                </div>
                <form onSubmit={handleSubmit} className="space-y-4">
                    <div>
                        <label className="block text-sm font-medium text-pcp-text-dim mb-1">Command Type</label>
                        <select
                            value={selectedCommand}
                            onChange={handleCommandChange}
                            className="w-full bg-pcp-dark border border-pcp-border rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-pcp-blue"
                        >
                            {Object.keys(COMMAND_SCHEMAS).map(cmd => <option key={cmd} value={cmd}>{cmd}</option>)}
                        </select>
                        <p className="text-xs text-pcp-text-dim mt-1">{currentSchema.description}</p>
                    </div>

                    {currentSchema.params.map(param => (
                        <div key={param.name}>
                            <label className="block text-sm font-medium text-pcp-text-dim mb-1">{param.name} {param.required && '*'}</label>
                            {param.type === 'select' ? (
                                <select name={param.name} value={params[param.name] || ''} onChange={handleParamChange} required={param.required} className="w-full bg-pcp-dark border border-pcp-border rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-pcp-blue">
                                  <option value="">Select...</option>
                                  {param.options?.map(opt => <option key={opt} value={opt}>{opt}</option>)}
                                </select>
                            ) : (
                                <input
                                    type={param.type}
                                    name={param.name}
                                    value={params[param.name] || ''}
                                    onChange={handleParamChange}
                                    placeholder={param.placeholder}
                                    required={param.required}
                                    className="w-full bg-pcp-dark border border-pcp-border rounded-md px-3 py-2 placeholder-pcp-text-dim focus:outline-none focus:ring-2 focus:ring-pcp-blue"
                                />
                            )}
                        </div>
                    ))}

                    <button type="submit" disabled={isSubmitting} className="w-full bg-pcp-blue text-white font-semibold py-2 rounded-md hover:bg-pcp-blue/80 disabled:bg-pcp-border disabled:cursor-not-allowed">
                        {isSubmitting ? 'Submitting...' : 'Execute Command'}
                    </button>
                </form>
                {lastResult && (
                    <div className="border-t border-pcp-border pt-4">
                        <h3 className="font-semibold text-pcp-text">Last Result</h3>
                        <div className="mt-2 p-3 bg-pcp-dark rounded-md text-sm space-y-1 font-mono">
                            <p>ID: {lastResult.id}</p>
                            <p>Status: {lastResult.status}</p>
                            <p className="text-pcp-text-dim">Rationale: {lastResult.rationale}</p>
                        </div>
                    </div>
                )}
            </div>

            <div className="bg-pcp-light-dark border-dashed border-2 border-pcp-blue/30 rounded-lg p-6 space-y-6 flex flex-col">
                <div>
                   <h2 className="text-xl font-bold text-pcp-text">AI-Assisted Command Generation</h2>
                   <p className="text-sm text-pcp-text-dim mt-1">Describe a complex task and let Gemini Pro suggest the command. (Thinking Mode)</p>
                </div>
                <textarea
                    value={naturalLanguageTask}
                    onChange={e => setNaturalLanguageTask(e.target.value)}
                    placeholder="e.g., 'A new marketing push for our client Acme Corp needs to go out on LinkedIn. The campaign ID is summer-blast-24. Then, scan their main website acme.com for any new issues.'"
                    className="w-full flex-grow bg-pcp-dark border border-pcp-border rounded-md px-3 py-2 placeholder-pcp-text-dim focus:outline-none focus:ring-2 focus:ring-pcp-blue resize-none"
                    rows={6}
                ></textarea>
                {analysisError && <p className="text-sm text-pcp-red">{analysisError}</p>}
                <button onClick={handleAnalyzeTask} disabled={isAnalyzing} className="w-full bg-pcp-blue/20 text-pcp-blue border border-pcp-blue font-semibold py-2 rounded-md hover:bg-pcp-blue/30 disabled:opacity-50 disabled:cursor-not-allowed">
                    {isAnalyzing ? 'Analyzing with Gemini...' : 'Analyze & Suggest Command'}
                </button>
            </div>
        </div>
    );
};

export default CommandCenterView;
