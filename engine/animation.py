class Animation:
    def __init__(self, name, fps, loop, frames):
        """
        Initializes an Animation object.
        
        Args:
            name (str): Name of the animation (e.g. "idle", "wave").
            fps (float): Frames per second.
            loop (bool): Whether the animation loops continuously.
            frames (list): List of [row, col] coordinates referencing the spritesheet.
        """
        self.name = name
        self.fps = fps
        self.loop = loop
        self.frames = frames
        self.current_frame_index = 0
        self.elapsed_time = 0.0
        self.is_playing = True
        self.is_finished = False

    def play(self):
        """Resumes playback of the animation."""
        self.is_playing = True

    def pause(self):
        """Pauses playback of the animation."""
        self.is_playing = False

    def stop(self):
        """Stops the animation and resets it to the first frame."""
        self.is_playing = False
        self.reset()

    def restart(self):
        """Resets the animation and starts playing from the beginning."""
        self.reset()
        self.play()

    def update(self, dt):
        """
        Updates the frame counter based on elapsed delta time.
        
        Args:
            dt (float): Time elapsed since the last update in seconds.
        """
        if not self.is_playing or (self.is_finished and not self.loop):
            return

        self.elapsed_time += dt
        frame_duration = 1.0 / max(self.fps, 0.1)

        while self.elapsed_time >= frame_duration:
            self.elapsed_time -= frame_duration
            if self.loop:
                self.current_frame_index = (self.current_frame_index + 1) % len(self.frames)
            else:
                if self.current_frame_index < len(self.frames) - 1:
                    self.current_frame_index += 1
                else:
                    self.is_finished = True
                    break

    def get_current_frame(self):
        """
        Returns the current frame coordinates [row, col].
        """
        if not self.frames:
            return [0, 0]
        return self.frames[self.current_frame_index]

    def reset(self):
        """Resets the animation play states to the starting frame."""
        self.current_frame_index = 0
        self.elapsed_time = 0.0
        self.is_finished = False
