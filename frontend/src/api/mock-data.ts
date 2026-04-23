import type {
  GenerationResult,
  TranscriptSegment,
  StructuredNote,
  ExamHint,
  CoverageModule,
  PracticeFlashcard,
  PracticeQuizItem,
  LectureHistoryItem,
} from '@/types';

// ── Transcript Segments ──
export const mockTranscriptSegments: TranscriptSegment[] = [
  { segment_id: 'seg_0001', start_sec: 0, end_sec: 12.5, text: "Welcome everyone to today's lecture on data structures and algorithms. Today we're going to cover a fundamental concept — binary search trees." },
  { segment_id: 'seg_0002', start_sec: 12.5, end_sec: 28.3, text: "A binary search tree, or BST, is a node-based binary tree data structure which has the following properties: The left subtree of a node contains only nodes with keys lesser than the node's key." },
  { segment_id: 'seg_0003', start_sec: 28.3, end_sec: 45.1, text: "The right subtree of a node contains only nodes with keys greater than the node's key. Both the left and right subtrees must also be binary search trees. This recursive property is what makes them powerful." },
  { segment_id: 'seg_0004', start_sec: 45.1, end_sec: 62.8, text: "The time complexity of search, insert, and delete operations in a BST is O(h) where h is the height of the tree. In the best case, this is O(log n) for a balanced tree." },
  { segment_id: 'seg_0005', start_sec: 62.8, end_sec: 80.4, text: "However, in the worst case — when the tree becomes skewed like a linked list — the time complexity degrades to O(n). This is why we need balanced BSTs like AVL trees and Red-Black trees." },
  { segment_id: 'seg_0006', start_sec: 80.4, end_sec: 98.2, text: "Let me now discuss the three types of tree traversals: in-order, pre-order, and post-order. In-order traversal of a BST gives nodes in non-decreasing order, which is extremely useful for sorting." },
  { segment_id: 'seg_0007', start_sec: 98.2, end_sec: 115.7, text: "For the mid-term exam, make sure you can trace through insertion and deletion operations on a BST. I will definitely include questions on tree traversals and their time complexities." },
  { segment_id: 'seg_0008', start_sec: 115.7, end_sec: 132.1, text: "Now let's look at AVL trees. An AVL tree is a self-balancing binary search tree where the difference between heights of left and right subtrees cannot be more than one for all nodes." },
  { segment_id: 'seg_0009', start_sec: 132.1, end_sec: 150.0, text: "AVL trees use rotations to maintain balance after every insertion and deletion. There are four types of rotations: Left rotation, Right rotation, Left-Right rotation, and Right-Left rotation." },
  { segment_id: 'seg_0010', start_sec: 150.0, end_sec: 168.3, text: "The advantage of AVL trees over regular BSTs is guaranteed O(log n) time for all operations. The trade-off is the overhead of maintaining balance factors and performing rotations." },
  { segment_id: 'seg_0011', start_sec: 168.3, end_sec: 185.9, text: "Red-Black trees are another type of self-balancing BST. They guarantee O(log n) operations but are less rigidly balanced than AVL trees, making insertions and deletions faster on average." },
  { segment_id: 'seg_0012', start_sec: 185.9, end_sec: 200.0, text: "In the final exam, expect questions comparing BST, AVL, and Red-Black trees. Understanding when to use each data structure is a critical skill for any software engineer." },
];

// ── Structured Notes ──
export const mockNotes: StructuredNote[] = [
  {
    module: 'Binary Search Trees',
    content: '**Binary Search Tree (BST)** is a node-based data structure with ordered properties:\n\n- Left subtree: keys < parent key\n- Right subtree: keys > parent key\n- Both subtrees are also valid BSTs (recursive invariant)\n\n**Time complexity**: O(h) for search, insert, delete — where h = tree height. Best case O(log n) for balanced trees; worst case O(n) for skewed trees.',
    references: [
      { segment_id: 'seg_0002', start_sec: 12.5, end_sec: 28.3, quote: "A binary search tree, or BST, is a node-based binary tree data structure", confidence: 0.95 },
      { segment_id: 'seg_0004', start_sec: 45.1, end_sec: 62.8, quote: "The time complexity of search, insert, and delete operations in a BST is O(h)", confidence: 0.92 },
    ],
    source_refs: ['00:12-00:28 (seg_0002)', '00:45-01:02 (seg_0004)'],
    confidence_score: 0.91,
    confidence_label: 'HIGH',
    confidence_reason: 'strong syllabus alignment; good transcript overlap; specific content; label HIGH',
  },
  {
    module: 'Tree Traversals',
    content: '**Three fundamental traversal orders:**\n\n1. **In-order** (Left → Root → Right): yields sorted output for BSTs\n2. **Pre-order** (Root → Left → Right): used for tree copying and serialization\n3. **Post-order** (Left → Right → Root): used for tree deletion\n\nIn-order traversal of a BST produces nodes in non-decreasing order — a key property for sorting applications.',
    references: [
      { segment_id: 'seg_0006', start_sec: 80.4, end_sec: 98.2, quote: "In-order traversal of a BST gives nodes in non-decreasing order", confidence: 0.88 },
    ],
    source_refs: ['01:20-01:38 (seg_0006)'],
    confidence_score: 0.82,
    confidence_label: 'HIGH',
    confidence_reason: 'strong syllabus alignment; good transcript overlap; specific content; label HIGH',
  },
  {
    module: 'AVL Trees',
    content: '**AVL Tree** — a self-balancing BST maintaining strict balance:\n\n- Height difference between left and right subtrees ≤ 1 for every node\n- Uses **rotations** for rebalancing: Left, Right, Left-Right, Right-Left\n- Guarantees **O(log n)** time for all search/insert/delete operations\n- Trade-off: overhead of maintaining balance factors and rotation cost',
    references: [
      { segment_id: 'seg_0008', start_sec: 115.7, end_sec: 132.1, quote: "An AVL tree is a self-balancing binary search tree", confidence: 0.93 },
      { segment_id: 'seg_0009', start_sec: 132.1, end_sec: 150.0, quote: "AVL trees use rotations to maintain balance", confidence: 0.9 },
    ],
    source_refs: ['01:55-02:12 (seg_0008)', '02:12-02:30 (seg_0009)'],
    confidence_score: 0.88,
    confidence_label: 'HIGH',
    confidence_reason: 'strong syllabus alignment; good transcript overlap; specific content; label HIGH',
  },
  {
    module: 'Red-Black Trees',
    content: '**Red-Black Tree** — another self-balancing BST:\n\n- Less rigidly balanced than AVL trees\n- Guarantees **O(log n)** operations\n- Faster insertions/deletions on average (fewer rotations)\n- Used in standard library implementations (e.g., Java TreeMap, C++ std::map)',
    references: [
      { segment_id: 'seg_0011', start_sec: 168.3, end_sec: 185.9, quote: "Red-Black trees guarantee O(log n) operations", confidence: 0.85 },
    ],
    source_refs: ['02:48-03:05 (seg_0011)'],
    confidence_score: 0.72,
    confidence_label: 'MEDIUM',
    confidence_reason: 'partial syllabus alignment; moderate transcript overlap; specific content; label MEDIUM',
  },
];

// ── Exam Hints ──
export const mockExamHints: ExamHint[] = [
  {
    hint: 'BST insertion and deletion tracing will appear on the mid-term',
    module: 'Binary Search Trees',
    urgency: 'HIGH',
    reason: 'Instructor explicitly stated "I will definitely include questions on tree traversals" during lecture.',
  },
  {
    hint: 'Comparison of BST vs AVL vs Red-Black trees expected in final exam',
    module: 'Self-Balancing Trees',
    urgency: 'HIGH',
    reason: 'Direct mention: "In the final exam, expect questions comparing BST, AVL, and Red-Black trees."',
  },
  {
    hint: 'Tree traversal time complexities — know all three orders',
    module: 'Tree Traversals',
    urgency: 'MEDIUM',
    reason: 'Strong emphasis on traversal types and their practical applications.',
  },
];

// ── Coverage Modules ──
export const mockCoverageModules: CoverageModule[] = [
  {
    module_name: 'Module 1: Introduction to Trees',
    coverage_percent: 85.2,
    status: 'Covered',
    evidence_count: 4,
    top_evidence_snippets: [
      { segment_id: 'seg_0001', start_sec: 0, end_sec: 12.5, text: "Welcome everyone to today's lecture on data structures and algorithms.", score: 0.82 },
      { segment_id: 'seg_0002', start_sec: 12.5, end_sec: 28.3, text: "A binary search tree, or BST, is a node-based binary tree data structure", score: 0.91 },
    ],
  },
  {
    module_name: 'Module 2: Binary Search Trees',
    coverage_percent: 92.7,
    status: 'Covered',
    evidence_count: 6,
    top_evidence_snippets: [
      { segment_id: 'seg_0003', start_sec: 28.3, end_sec: 45.1, text: "Both the left and right subtrees must also be binary search trees.", score: 0.94 },
      { segment_id: 'seg_0004', start_sec: 45.1, end_sec: 62.8, text: "The time complexity of search, insert, and delete operations in a BST is O(h)", score: 0.89 },
    ],
  },
  {
    module_name: 'Module 3: Balanced Trees (AVL)',
    coverage_percent: 78.4,
    status: 'Covered',
    evidence_count: 3,
    top_evidence_snippets: [
      { segment_id: 'seg_0008', start_sec: 115.7, end_sec: 132.1, text: "An AVL tree is a self-balancing binary search tree", score: 0.87 },
    ],
  },
  {
    module_name: 'Module 4: Red-Black Trees',
    coverage_percent: 45.1,
    status: 'Partial',
    evidence_count: 2,
    top_evidence_snippets: [
      { segment_id: 'seg_0011', start_sec: 168.3, end_sec: 185.9, text: "Red-Black trees are another type of self-balancing BST.", score: 0.72 },
    ],
  },
  {
    module_name: 'Module 5: B-Trees and B+ Trees',
    coverage_percent: 8.3,
    status: 'Missing',
    evidence_count: 0,
    top_evidence_snippets: [],
  },
  {
    module_name: 'Module 6: Graph Algorithms',
    coverage_percent: 0,
    status: 'Missing',
    evidence_count: 0,
    top_evidence_snippets: [],
  },
];

// ── Flashcards ──
export const mockFlashcards: PracticeFlashcard[] = [
  { question: 'What are the three properties of a Binary Search Tree?', answer: '1) Left subtree contains only keys less than the node key. 2) Right subtree contains only keys greater than the node key. 3) Both subtrees must also be valid BSTs.', module: 'Binary Search Trees', difficulty: 'easy' },
  { question: 'What is the time complexity of BST operations in the best and worst case?', answer: 'Best case: O(log n) for balanced trees. Worst case: O(n) for skewed trees (degenerates to linked list).', module: 'Binary Search Trees', difficulty: 'medium' },
  { question: 'What does in-order traversal of a BST produce?', answer: 'Nodes in non-decreasing (sorted) order.', module: 'Tree Traversals', difficulty: 'easy' },
  { question: 'What is the balance condition for AVL trees?', answer: 'The height difference between left and right subtrees cannot be more than 1 for all nodes.', module: 'AVL Trees', difficulty: 'medium' },
  { question: 'Name the four types of AVL rotations.', answer: 'Left rotation, Right rotation, Left-Right (double) rotation, and Right-Left (double) rotation.', module: 'AVL Trees', difficulty: 'hard' },
  { question: 'How do Red-Black trees compare to AVL trees?', answer: 'Red-Black trees are less rigidly balanced, resulting in faster insertions/deletions but slightly slower lookups compared to AVL trees.', module: 'Red-Black Trees', difficulty: 'medium' },
  { question: 'What is the guaranteed time complexity for operations in AVL and Red-Black trees?', answer: 'Both guarantee O(log n) for search, insert, and delete operations.', module: 'Self-Balancing Trees', difficulty: 'easy' },
  { question: 'When would you prefer a Red-Black tree over an AVL tree?', answer: 'When the workload involves frequent insertions and deletions, since Red-Black trees require fewer rotations on average.', module: 'Red-Black Trees', difficulty: 'hard' },
  { question: 'Define pre-order and post-order traversal.', answer: 'Pre-order: Root → Left → Right (used for tree copying). Post-order: Left → Right → Root (used for tree deletion).', module: 'Tree Traversals', difficulty: 'medium' },
  { question: 'Why might a BST degrade to O(n) performance?', answer: 'When elements are inserted in sorted order, the tree becomes skewed (essentially a linked list), making the height equal to n.', module: 'Binary Search Trees', difficulty: 'medium' },
];

// ── Quiz Items ──
export const mockQuizItems: PracticeQuizItem[] = [
  {
    id: 'q1', type: 'mcq', module: 'Binary Search Trees', difficulty: 'easy',
    question: 'What is the worst-case time complexity of searching in a BST?',
    options: ['O(1)', 'O(log n)', 'O(n)', 'O(n²)'],
    correct_index: 2,
    explanation: 'In the worst case (skewed tree), BST search degrades to O(n).',
  },
  {
    id: 'q2', type: 'true_false', module: 'Binary Search Trees', difficulty: 'easy',
    question: 'In-order traversal of a BST always gives nodes in ascending order.',
    answer: true,
    explanation: 'By definition, in-order traversal visits left, root, right — yielding sorted output for BSTs.',
  },
  {
    id: 'q3', type: 'short_answer', module: 'AVL Trees', difficulty: 'medium',
    question: 'What is the maximum allowed height difference between subtrees in an AVL tree?',
    answer: '1',
    explanation: 'AVL trees enforce that the balance factor (height difference) is at most 1.',
  },
  {
    id: 'q4', type: 'mcq', module: 'Tree Traversals', difficulty: 'medium',
    question: 'Which traversal order visits Root → Left → Right?',
    options: ['In-order', 'Pre-order', 'Post-order', 'Level-order'],
    correct_index: 1,
    explanation: 'Pre-order traversal processes the root first, then left subtree, then right subtree.',
  },
  {
    id: 'q5', type: 'true_false', module: 'Red-Black Trees', difficulty: 'medium',
    question: 'Red-Black trees are more strictly balanced than AVL trees.',
    answer: false,
    explanation: 'AVL trees enforce stricter balance. Red-Black trees allow more imbalance but require fewer rotations.',
  },
  {
    id: 'q6', type: 'mcq', module: 'AVL Trees', difficulty: 'hard',
    question: 'How many types of rotations does an AVL tree use for rebalancing?',
    options: ['2', '3', '4', '6'],
    correct_index: 2,
    explanation: 'AVL trees use 4 rotation types: Left, Right, Left-Right, and Right-Left.',
  },
  {
    id: 'q7', type: 'short_answer', module: 'Binary Search Trees', difficulty: 'easy',
    question: 'In a BST, where are nodes with keys smaller than the root stored?',
    answer: 'left subtree',
    explanation: 'By BST property, all keys in the left subtree are less than the root key.',
  },
  {
    id: 'q8', type: 'mcq', module: 'Self-Balancing Trees', difficulty: 'hard',
    question: 'Which data structure is commonly used in the implementation of std::map in C++?',
    options: ['Hash Table', 'AVL Tree', 'Red-Black Tree', 'Skip List'],
    correct_index: 2,
    explanation: 'Most C++ standard library implementations use Red-Black trees for ordered associative containers.',
  },
  {
    id: 'q9', type: 'true_false', module: 'Binary Search Trees', difficulty: 'medium',
    question: 'Deleting a node with two children in a BST requires finding the in-order successor or predecessor.',
    answer: true,
    explanation: 'The standard BST deletion algorithm replaces the node with its in-order successor (or predecessor) to maintain BST property.',
  },
  {
    id: 'q10', type: 'mcq', module: 'Tree Traversals', difficulty: 'medium',
    question: 'Which traversal is most useful for deleting an entire tree?',
    options: ['Pre-order', 'In-order', 'Post-order', 'Level-order'],
    correct_index: 2,
    explanation: 'Post-order traversal processes children before the parent, making it safe to delete nodes bottom-up.',
  },
];

// ── Full Generation Result ──
export const mockGenerationResult: GenerationResult = {
  id: 'gen_001',
  title: 'Data Structures: Binary Search Trees & Balanced Trees',
  summary: 'This lecture covered binary search trees (BSTs), their properties and time complexities, tree traversal methods (in-order, pre-order, post-order), and self-balancing BST variants including AVL trees and Red-Black trees. Key exam topics were highlighted including BST operation tracing and comparative analysis of tree types.',
  filtered_count: 7,
  language: 'en',
  notes: mockNotes,
  exam_radar: mockExamHints,
  transcript_segments: mockTranscriptSegments,
  transcript_text: mockTranscriptSegments.map((s) => s.text).join(' '),
  syllabus_coverage: {
    modules: mockCoverageModules,
    summary: { covered: 3, partial: 1, missing: 2, total: 6 },
  },
  practice: {
    metadata: {
      title: 'Data Structures: Binary Search Trees & Balanced Trees',
      language: 'en',
      generated_from_modules: ['Binary Search Trees', 'Tree Traversals', 'AVL Trees', 'Red-Black Trees'],
    },
    flashcards: mockFlashcards,
    quiz: mockQuizItems,
  },
  provider: 'groq',
  created_at: '2026-04-22T14:30:00Z',
  lecture_filename: 'dsa_lecture_05.mp3',
};

// ── Lecture History ──
export const mockLectureHistory: LectureHistoryItem[] = [
  {
    id: 'gen_001',
    title: 'Data Structures: Binary Search Trees & Balanced Trees',
    provider: 'groq',
    language: 'English',
    lecture_filename: 'dsa_lecture_05.mp3',
    created_at: '2026-04-22T14:30:00Z',
    notes_count: 4,
    exam_hints_count: 3,
    course: 'CS201 — Data Structures',
  },
  {
    id: 'gen_002',
    title: 'Operating Systems: Process Scheduling Algorithms',
    provider: 'openai',
    language: 'English',
    lecture_filename: 'os_lecture_12.mp4',
    created_at: '2026-04-20T09:15:00Z',
    notes_count: 6,
    exam_hints_count: 2,
    course: 'CS305 — Operating Systems',
  },
  {
    id: 'gen_003',
    title: 'Linear Algebra: Eigenvalues and Eigenvectors',
    provider: 'groq',
    language: 'English',
    lecture_filename: 'math_eigen.m4a',
    created_at: '2026-04-18T16:45:00Z',
    notes_count: 5,
    exam_hints_count: 4,
    course: 'MATH220 — Linear Algebra',
  },
  {
    id: 'gen_004',
    title: 'Introduction to Machine Learning: Gradient Descent',
    provider: 'groq',
    language: 'English',
    lecture_filename: 'ml_lecture_03.wav',
    created_at: '2026-04-15T11:00:00Z',
    notes_count: 7,
    exam_hints_count: 1,
    course: 'CS410 — Machine Learning',
  },
  {
    id: 'gen_005',
    title: 'Análisis de redes neuronales convolucionales',
    provider: 'openai',
    language: 'Spanish',
    lecture_filename: 'dl_cnn_lecture.mp3',
    created_at: '2026-04-12T13:20:00Z',
    notes_count: 3,
    exam_hints_count: 2,
    course: 'CS410 — Machine Learning',
  },
];
