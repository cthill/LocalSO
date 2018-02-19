class BoundingBox:
    def __init__(self, x, y, w, h):
        self.x = x
        self.y = y
        self.w = w
        self.h = h

    def check_collision(self, other):
        return (self.x < other.x + other.w and
                self.x + self.w > other.x and
                self.y < other.y + other.h and
                self.y + self.h > other.y)

    def check_collision_point(self, x, y):
        return (x > self.x and
                x < self.x + self.w and
                y > self.y and
                y < self.y + self.h)

    def move(self, x, y):
        self.x = x
        self.y = y

    def resize(self, w, h):
        self.w = w
        self.h = h

    def left(self):
        return self.x

    def right(self):
        return self.x + self.w

    def top(self):
        return self.y

    def bottom(self):
        return self.y + self.h

    def hcenter(self):
        return self.x + self.w / 2

    def vcenter(self):
        return self.y + self.h / 2
