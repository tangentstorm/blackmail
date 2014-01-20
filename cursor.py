

class Cursor(object):

    def __init__(self, view):
        self.view = view
        self.moveToTop()
        
    def moveToTop(self):
        self.position = self.view.indexFirst()

    def moveToBottom(self):
        self.position = self.view.indexLast()

    def moveUp(self):
        try:
            self.position = self.view.indexPrevious(self.position)
        except LookupError:
            pass
        
    def moveDown(self):
        try:
            self.position = self.view.indexNext(self.position)
        except LookupError:
            pass


    # or if you prefer a non-spatial metaphor:
    def moveNext(self): self.moveDown()
    def movePrevious(self): self.moveUp()
    def moveToStart(self): self.moveToTop()
    def moveToEnd(self): self.moveToBottom()
        

    def value(self):
        return self.view[self.position]



class ListView(object):
    
    def __init__(self, data):
        self.data = data
        self.zoomed = False

    def indexFirst(self):
        return self.indexNext(-1)

    def indexLast(self):
        return self.indexPrevious(len(self.data))

    def isVisible(self, i):
        return True

    def __getitem__(self, key):
        return self.data[key]

    ## cursor interface


    def indexNext(self, index):
        for next in range(index+1, len(self.data)):
            if self.isVisible(next): return next
        return index

    def indexPrevious(self, index):
        for next in range(index-1, -1, -1):
            if self.isVisible(next): return next
        return index



class ZoomView(ListView):
    """
    This allows you to move through a subselection of items.
    It's modelled after the 'Zoom' feature in the Pine mail client.
    """

    def __init__(self, data):
        ListView.__init__(self, data)
        self.zoomed = False
        
    ## selection interface

    def selectWhere(self, test):
        self.selected = {}
        for i, row in enumerate(self.data):
            self.selected[i] = bool(test(row))

    ## zooming interface

    def zoom(self):
        self.zoomed = True

    def unzoom(self):
        self.zoomed = False

    def visible(self):
        if self.zoomed:
            [(yield each) for i,each in enumerate(self.data)
             if self.selected[i]]
        else:
            [(yield each) for each in self.data]

    def isVisible(self, index):
        assert 0 <= index < len(self.data), "invalid index: %s" % index
        if self.zoomed:
            return self.selected[index]
        else:
            return True


def ListCursor(data):
    return Cursor(ListView(data))


