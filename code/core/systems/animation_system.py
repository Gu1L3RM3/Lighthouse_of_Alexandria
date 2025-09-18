from core.ecs import System
from core.components.sprite import Sprite
from core.components.animation_sprite import AnimateSprite

class AnimationSystem(System):
    def update(self, entity_mn, dt: float):
        entities = entity_mn.get_entities_with(Sprite, AnimateSprite)

        for entity in entities:
            anim: AnimateSprite = entity.get(AnimateSprite)
            spr: Sprite = entity.get(Sprite)

            if anim.current_animation is None or anim.done:
                continue

            frames = anim.animations.get(anim.current_animation, [])
            if not frames:
                continue

            anim.time_acc += dt
            frame_duration = 1.0 / anim.fps

            while anim.time_acc >= frame_duration:
                anim.time_acc -= frame_duration
                anim.current_frame += 1

                if anim.current_frame >= len(frames):
                    if anim.loop:
                        anim.current_frame = 0
                    else:
                        anim.current_frame = len(frames) - 1
                        anim.done = True
                        break 
            
            
            anim.current_frame = min(anim.current_frame, len(frames) - 1)
            spr.image = frames[anim.current_frame]