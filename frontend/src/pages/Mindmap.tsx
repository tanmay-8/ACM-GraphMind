import { useEffect, useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  ReactFlow,
  Controls,
  Background,
  BackgroundVariant,
  useNodesState,
  useEdgesState,
  MarkerType,
  Position,
  type Node,
  type Edge,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import { useAuth } from '../contexts/AuthContext';
import { memoryAPI } from '../lib/api';
import { Button } from '../components/ui/button';
import { Card } from '../components/ui/card';
import { ArrowLeft, RefreshCw, Loader2 } from 'lucide-react';

// Define node colors by type
const nodeColors: Record<string, string> = {
  User: '#3b82f6', // blue
  Asset: '#10b981', // green
  Goal: '#f59e0b', // amber
  Transaction: '#8b5cf6', // purple
  RiskProfile: '#ef4444', // red
};

export default function Mindmap() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [nodes, setNodes, onNodesChange] = useNodesState<Node>([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState<Edge>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadMindmap = useCallback(async () => {
    if (!user) return;

    setIsLoading(true);
    setError(null);

    try {
      const data = await memoryAPI.getMindmap();

      // Transform nodes for ReactFlow
      const flowNodes: Node[] = data.nodes.map((node: any, index: number) => {
        // Calculate position in a circular layout
        const angle = (index / data.nodes.length) * 2 * Math.PI;
        const radius = 250;
        const x = Math.cos(angle) * radius + 400;
        const y = Math.sin(angle) * radius + 300;

        return {
          id: node.id,
          type: 'default',
          position: { x, y },
          data: {
            label: (
              <div className="text-center">
                <div className="font-semibold text-sm">{node.label}</div>
                <div className="text-xs text-gray-500">{node.type}</div>
              </div>
            ),
          },
          style: {
            background: nodeColors[node.type] || '#6b7280',
            color: 'white',
            border: '2px solid white',
            borderRadius: '8px',
            padding: '10px',
            fontSize: '12px',
            minWidth: '120px',
          },
          sourcePosition: Position.Right,
          targetPosition: Position.Left,
        };
      });

      // Transform edges for ReactFlow
      const flowEdges: Edge[] = data.edges.map((edge: any) => ({
        id: edge.id,
        source: edge.source,
        target: edge.target,
        label: edge.label,
        type: 'smoothstep',
        animated: true,
        style: { stroke: '#94a3b8', strokeWidth: 2 },
        markerEnd: {
          type: MarkerType.ArrowClosed,
          color: '#94a3b8',
        },
        labelStyle: {
          fill: '#64748b',
          fontSize: 10,
          fontWeight: 500,
        },
        labelBgStyle: {
          fill: 'white',
          fillOpacity: 0.8,
        },
      }));

      setNodes(flowNodes);
      setEdges(flowEdges);
    } catch (err: any) {
      console.error('Failed to load mindmap:', err);
      setError(err.response?.data?.detail || 'Failed to load mindmap');
    } finally {
      setIsLoading(false);
    }
  }, [user, setNodes, setEdges]);

  useEffect(() => {
    loadMindmap();
  }, [loadMindmap]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 dark:from-gray-900 dark:to-gray-800">
      {/* Header */}
      <header className="border-b bg-white/80 dark:bg-gray-900/80 backdrop-blur-sm sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Button
              variant="outline"
              size="sm"
              onClick={() => navigate('/chat')}
              className="gap-2"
            >
              <ArrowLeft className="w-4 h-4" />
              Back to Chat
            </Button>
            <div>
              <h1 className="text-lg font-semibold">Knowledge Graph</h1>
              <p className="text-xs text-gray-500 dark:text-gray-400">
                Visualize your financial memory
              </p>
            </div>
          </div>

          <Button
            variant="outline"
            size="sm"
            onClick={loadMindmap}
            disabled={isLoading}
            className="gap-2"
          >
            {isLoading ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <RefreshCw className="w-4 h-4" />
            )}
            Refresh
          </Button>
        </div>
      </header>

      {/* Content */}
      <main className="h-[calc(100vh-73px)]">
        {isLoading && nodes.length === 0 ? (
          <div className="h-full flex items-center justify-center">
            <Card className="p-8 text-center">
              <Loader2 className="w-12 h-12 animate-spin mx-auto mb-4 text-blue-600" />
              <p className="text-gray-600 dark:text-gray-400">Loading your knowledge graph...</p>
            </Card>
          </div>
        ) : error ? (
          <div className="h-full flex items-center justify-center">
            <Card className="p-8 text-center max-w-md">
              <div className="w-12 h-12 bg-red-100 dark:bg-red-900/20 rounded-full flex items-center justify-center mx-auto mb-4">
                <span className="text-red-600 text-2xl">⚠️</span>
              </div>
              <h2 className="text-lg font-semibold mb-2">Error Loading Graph</h2>
              <p className="text-gray-600 dark:text-gray-400 mb-4">{error}</p>
              <Button onClick={loadMindmap}>Try Again</Button>
            </Card>
          </div>
        ) : nodes.length === 0 ? (
          <div className="h-full flex items-center justify-center">
            <Card className="p-8 text-center max-w-md">
              <div className="w-16 h-16 bg-gray-100 dark:bg-gray-800 rounded-full flex items-center justify-center mx-auto mb-4">
                <span className="text-4xl">🌐</span>
              </div>
              <h2 className="text-lg font-semibold mb-2">No Data Yet</h2>
              <p className="text-gray-600 dark:text-gray-400 mb-4">
                Start chatting to build your financial knowledge graph. Share information about
                your investments, goals, and transactions.
              </p>
              <Button onClick={() => navigate('/chat')}>Go to Chat</Button>
            </Card>
          </div>
        ) : (
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            fitView
            attributionPosition="bottom-left"
          >
            <Controls />
            <Background variant={BackgroundVariant.Dots} gap={12} size={1} />
          </ReactFlow>
        )}
      </main>

      {/* Legend */}
      {nodes.length > 0 && (
        <div className="fixed bottom-4 left-4 bg-white dark:bg-gray-800 rounded-lg shadow-lg p-4 max-w-xs">
          <h3 className="font-semibold text-sm mb-2">Node Types</h3>
          <div className="space-y-1">
            {Object.entries(nodeColors).map(([type, color]) => (
              <div key={type} className="flex items-center gap-2 text-xs">
                <div
                  className="w-3 h-3 rounded-full border border-white"
                  style={{ backgroundColor: color }}
                />
                <span>{type}</span>
              </div>
            ))}
          </div>
          <div className="mt-3 pt-3 border-t text-xs text-gray-500">
            <p>Drag nodes to rearrange</p>
            <p>Scroll to zoom in/out</p>
          </div>
        </div>
      )}
    </div>
  );
}
