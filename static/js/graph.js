// vis-network.js Graph Engine for OffboardGuard
class OffboardGraphExplorer {
  constructor(containerId, options = {}) {
    this.container = document.getElementById(containerId);
    this.network = null;
    this.nodesDataSet = new vis.DataSet([]);
    this.edgesDataSet = new vis.DataSet([]);
    this.rawNodes = [];
    this.rawEdges = [];
    this.activeFilters = {
      Employee: true,
      SlackGroup: true,
      OktaGroup: true,
      AWSRole: true,
      CloudResource: true
    };
    this.options = options;
  }

  getNodeStyle(node) {
    const type = node.type || node.label || 'Unknown';
    switch (type) {
      case 'Employee':
        const isOffboarded = node.status === 'offboarded';
        return {
          shape: 'dot',
          size: isOffboarded ? 24 : 18,
          color: {
            background: isOffboarded ? '#FEE2E2' : '#EFF6FF',
            border: isOffboarded ? '#DC2626' : '#2563EB',
            highlight: { background: '#FEF2F2', border: '#B91C1C' }
          },
          borderWidth: isOffboarded ? 3 : 2,
          font: { color: isOffboarded ? '#991B1B' : '#1E3A8A', face: 'Inter, system-ui', size: 14, bold: isOffboarded }
        };
      case 'SlackGroup':
        return {
          shape: 'diamond',
          size: 16,
          color: { background: '#F3E8FF', border: '#7C3AED', highlight: { background: '#DDD6FE', border: '#6D28D9' } },
          borderWidth: 2,
          font: { color: '#5B21B6', face: 'Inter, system-ui', size: 12 }
        };
      case 'OktaGroup':
        return {
          shape: 'box',
          margin: 10,
          color: { background: '#EEF2FF', border: '#4F46E5', highlight: { background: '#E0E7FF', border: '#4338CA' } },
          borderWidth: 2,
          shapeProperties: { borderRadius: 6 },
          font: { color: '#3730A3', face: 'Inter, system-ui', size: 12 }
        };
      case 'AWSRole':
        return {
          shape: 'triangle',
          size: 18,
          color: { background: '#FEF3C7', border: '#D97706', highlight: { background: '#FDE68A', border: '#B45309' } },
          borderWidth: 2,
          font: { color: '#92400E', face: 'Inter, system-ui', size: 12 }
        };
      case 'CloudResource':
        const sensitivity = node.sensitivity || 'low';
        let bg = '#F3F4F6', border = '#6B7280';
        if (sensitivity === 'critical') { bg = '#FEE2E2'; border = '#991B1B'; }
        else if (sensitivity === 'high') { bg = '#FFEDD5'; border = '#C2410C'; }
        else if (sensitivity === 'medium') { bg = '#FEF9C3'; border = '#854D0E'; }

        return {
          shape: 'ellipse',
          color: { background: bg, border: border, highlight: { background: bg, border: border } },
          borderWidth: 3,
          font: { color: '#111827', face: 'Inter, system-ui', size: 13, bold: true }
        };
      default:
        return {
          shape: 'dot',
          size: 14,
          color: { background: '#E5E7EB', border: '#9CA3AF' }
        };
    }
  }

  loadData(data) {
    if (!data || !data.nodes) return;
    this.rawNodes = data.nodes;
    this.rawEdges = data.edges || [];
    this.render();
  }

  render() {
    const filteredNodes = this.rawNodes.filter(n => this.activeFilters[n.type] !== false);
    const visibleNodeIds = new Set(filteredNodes.map(n => n.id));

    const visNodes = filteredNodes.map(n => {
      const style = this.getNodeStyle(n);
      return {
        id: n.id,
        label: n.name || n.id,
        title: `${n.type}: ${n.name || n.id} ${n.sensitivity ? `(${n.sensitivity})` : ''}`,
        ...style
      };
    });

    const filteredEdges = this.rawEdges.filter(e => visibleNodeIds.has(e.from) && visibleNodeIds.has(e.to));
    const visEdges = filteredEdges.map(e => {
      return {
        id: e.id,
        from: e.from,
        to: e.to,
        label: e.label || '',
        arrows: 'to',
        font: { size: 10, align: 'top', color: '#6B7280' },
        color: { color: '#D1D5DB', highlight: '#7C3AED' },
        width: 1.5,
        smooth: { type: 'cubicBezier' }
      };
    });

    this.nodesDataSet.clear();
    this.nodesDataSet.add(visNodes);
    this.edgesDataSet.clear();
    this.edgesDataSet.add(visEdges);

    const visData = { nodes: this.nodesDataSet, edges: this.edgesDataSet };
    const visOptions = {
      nodes: {
        font: { size: 13 }
      },
      edges: {
        smooth: { forceDirection: 'none' }
      },
      physics: {
        solver: 'forceAtlas2Based',
        forceAtlas2Based: {
          gravitationalConstant: -50,
          centralGravity: 0.01,
          springLength: 100,
          springConstant: 0.08
        },
        stabilization: { iterations: 150 }
      },
      interaction: {
        hover: true,
        tooltipDelay: 200,
        navigationButtons: true,
        keyboard: true
      }
    };

    if (!this.network) {
      this.network = new vis.Network(this.container, visData, visOptions);
      this.network.on("click", (params) => {
        if (params.nodes.length > 0) {
          const nodeId = params.nodes[0];
          const nodeData = this.rawNodes.find(n => n.id === nodeId);
          if (this.options.onNodeSelect) {
            this.options.onNodeSelect(nodeData);
          }
        }
      });
    } else {
      this.network.setData(visData);
    }
  }

  toggleFilter(nodeType, isEnabled) {
    this.activeFilters[nodeType] = isEnabled;
    this.render();
  }

  fit() {
    if (this.network) this.network.fit();
  }

  togglePhysics(enabled) {
    if (this.network) {
      this.network.setOptions({ physics: { enabled: enabled } });
    }
  }
}

window.OffboardGraphExplorer = OffboardGraphExplorer;
