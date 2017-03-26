

function Node(val) {
    this.value = val;
    this.next = null;
}



function enqueue(item) {
    this.size += 1;
    const node = new Node(item);
    if(this.tail) {
        this.tail.next = node;
        this.tail = node;
    } else {
        this.head = node;
        this.tail = node;
    }
}

function dequeue(item) {
    if(this.head) {
        
        const out = this.head;
        this.head = this.head.next;
        
        if(out === this.tail)
            this.tail = null;
        this.size -= 1;

        return out.value;
    } else {
        return null;
    }
}

function Queue() {

    this.head = null;
    this.tail = null;
    this.size = 0;

    this.enqueue = enqueue.bind(this);
    this.dequeue = dequeue.bind(this);

}

module.exports = Queue;

