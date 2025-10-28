
import React from 'react';
import { RUNBOOK_CONTENT } from '../constants';

// A very simple markdown-to-HTML converter for this specific use case
const SimpleMarkdown: React.FC<{ content: string }> = ({ content }) => {
    const lines = content.split('\n');
    const elements = lines.map((line, index) => {
        if (line.startsWith('# ')) {
            return <h1 key={index} className="text-3xl font-bold mt-6 mb-3 border-b border-pcp-border pb-2">{line.substring(2)}</h1>;
        }
        if (line.startsWith('## ')) {
            return <h2 key={index} className="text-2xl font-bold mt-5 mb-2">{line.substring(3)}</h2>;
        }
        if (line.startsWith('### ')) {
            return <h3 key={index} className="text-xl font-bold mt-4 mb-2">{line.substring(4)}</h3>;
        }
        if (line.startsWith('- ')) {
            return <li key={index} className="ml-6 list-disc">{line.substring(2)}</li>;
        }
        if (line.match(/^\d+\. /)) {
            return <li key={index} className="ml-6 list-decimal">{line.substring(line.indexOf(' ') + 1)}</li>;
        }
        if (line.trim() === '') {
            return <div key={index} className="h-4"></div>; // Represent empty lines as space
        }
        // Handle code blocks and inline code
        if (line.includes('`')) {
            const parts = line.split('`');
            return (
                <p key={index} className="text-pcp-text-dim leading-relaxed">
                    {parts.map((part, i) =>
                        i % 2 === 1 ? (
                            <code key={i} className="bg-pcp-border/50 text-pcp-blue font-mono px-1 py-0.5 rounded-sm text-sm">
                                {part}
                            </code>
                        ) : (
                            part
                        )
                    )}
                </p>
            );
        }
        return <p key={index} className="text-pcp-text-dim leading-relaxed">{line}</p>;
    });

    return <>{elements}</>;
};

export const RunbookView: React.FC = () => {
    return (
        <div className="bg-pcp-light-dark border border-pcp-border rounded-lg p-6 md:p-8 max-w-4xl mx-auto">
            <SimpleMarkdown content={RUNBOOK_CONTENT} />
        </div>
    );
};
