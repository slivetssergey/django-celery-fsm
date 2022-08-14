import logging

logger = logging.getLogger('fsm')


class BaseFSM:
    def get_model(self):
        if model := getattr(self, 'model'):
            return model
        raise AttributeError('Set `model` attribute')

    def get_steps(self):
        return []

    def __init__(self, *args, **kwargs):
        self.model = self.get_model()
        self.steps = self.get_steps()

    @classmethod
    def trigger(cls):
        fsm = cls()
        model = fsm.get_model()
        steps = fsm.get_steps()
        statuses = [step['status'] for step in steps]
        qs = model.objects.filter(status__in=statuses).order_by('id').values_list('id', flat=True)
        for instance_id in qs:
            cls.run(instance_id=instance_id)

    def get_step(self, name: str):
        step = next((step for step in self.steps if step['name'] == name), None)
        if not step:
            raise ValueError(f'No step {name} into FSM ...')
        return step

    def task_success(self, instance_id: int, name: str):
        pass

    def fail_task(self, instance_id: int, name: str, exc, einfo):
        pass

    def run_next_step(self, instance_id: int, current_name: str):
        logger.debug('Run next step %s %s' % (instance_id, current_name))
        step = self.get_step(current_name)
        if next_step := step.get('next'):
            if isinstance(next_step, list):
                for i in next_step:
                    self.run_step(instance_id=instance_id, name=i)
            else:
                self.run_step(instance_id=instance_id, name=next_step)
        else:
            logger.debug('No next step.')

    def call_callback(self, callback, instance_id: int):
        if callable(callback):
            callback(instance_id=instance_id)
        else:
            raise ValueError(f'Callback {callback} not callable')

    def step_callback(self, instance_id: int, current_name: str):
        step = self.get_step(current_name)
        if callback := step.get('callback'):
            if isinstance(callback, list):
                for callback_item in callback:
                    self.call_callback(callback_item, instance_id=instance_id)
            else:
                self.call_callback(callback, instance_id=instance_id)

    def run_step(self, instance_id: int, name: str):
        logger.info(f'Run step {name} of {self.__class__.__qualname__}. Instance_id: {instance_id}')
        step = self.get_step(name)
        instance = self.get_model().objects.filter(status=step['status'], pk=instance_id).first()
        if not instance:
            msg = 'Target instance not found. Id: %s, Status: %s' % (
                instance_id,
                step['status'],
            )
            raise ValueError(msg)

        fsm_name = f'{self.__class__.__module__}.{self.__class__.__qualname__}'
        step['task']().s(
            id=instance.id,
            app_label=instance._meta.app_label,
            model_name=instance._meta.model_name,
            fsm=fsm_name,
            step=step['name'],
            status=step['status'],
        ).apply_async()
        logger.info(
            f'Finish step {name} of {self.__class__.__qualname__}. Instance_id: {instance_id}'
        )

    def get_instance(self, instance_id: int):
        return self.model.objects.get(pk=instance_id)

    @classmethod
    def run(cls, instance_id: int):
        fsm = cls()
        instance = fsm.get_instance(instance_id)
        statuses = [step['status'] for step in fsm.steps]
        if instance.status not in statuses:
            raise ValueError('Incorrect FSM status')
        step = next(step for step in fsm.steps if step['status'] == instance.status)
        fsm.run_step(instance_id, step['name'])
