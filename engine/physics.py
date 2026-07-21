class PhysicsEngine:
    def __init__(self, x=0.0, y=0.0, width=128, height=128):
        """
        Coordinates pet physics.
        """
        self.x = float(x)
        self.y = float(y)
        self.vx = 0.0
        self.vy = 0.0
        
        # Physics constants
        self.gravity = 950.0  # Pixels per second squared
        self.friction = 0.92  # Ground friction factor per 1/60s frame
        self.bounce = 0.4     # Bounce elasticity
        
        self.width = width
        self.height = height
        self.is_grounded = False
        self.is_dragging = False
        self.is_static = False

    def update(self, dt, screen_width, screen_height):
        """
        Updates the positions based on kinematics.
        """
        if self.is_static:
            self.vx = 0.0
            self.vy = 0.0
            return

        if self.is_dragging:
            return  # Positions are set manually during drag

        # Apply gravity if not on ground
        if not self.is_grounded:
            self.vy += self.gravity * dt
        
        # Apply velocities
        self.x += self.vx * dt
        self.y += self.vy * dt

        # Ground collisions (e.g. taskbar boundary)
        ground_y = screen_height - self.height
        if self.y >= ground_y:
            self.y = ground_y
            self.vy = 0.0
            self.is_grounded = True
            
            # Decelerate horizontal velocity via friction on ground
            self.vx *= (self.friction ** (dt * 60.0))
            if abs(self.vx) < 1.0:
                self.vx = 0.0
        else:
            self.is_grounded = False

        # Left boundary check
        if self.x < 0:
            self.x = 0
            self.vx = -self.vx * self.bounce
            
        # Right boundary check
        elif self.x > screen_width - self.width:
            self.x = screen_width - self.width
            self.vx = -self.vx * self.bounce

        # Top boundary check (prevent launching off screen top)
        if self.y < 0:
            self.y = 0
            self.vy = 0.0

    def apply_impulse(self, vx, vy):
        """Applies a sudden velocity impulse (e.g. for Jumping or Throwing)."""
        self.vx = vx
        self.vy = vy
        if vy < 0:
            self.is_grounded = False

    def start_drag(self):
        """Stops motion when starting drag."""
        self.is_dragging = True
        self.vx = 0.0
        self.vy = 0.0
        self.is_grounded = False

    def end_drag(self, release_vx, release_vy):
        """Releases the pet with a specific velocity (momentum throw)."""
        self.is_dragging = False
        self.vx = release_vx
        self.vy = release_vy
