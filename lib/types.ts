export interface Node {
    id: string
    group?: string
    status?: string
    topics?: string[]
    x?: number
    y?: number
  }
  
  export interface Link {
    source: string | Node
    target: string | Node
    topics?: string[]
  }
  
  export interface GraphData {
    nodes: Node[]
    links: Link[]
  }
  
  
