from drf_yasg.inspectors import SwaggerAutoSchema

class TaggedAutoSchema(SwaggerAutoSchema):
    def get_tags(self, operation_keys=None):
        app_label = self.view.__module__.split('.')[0]  # This gets the app name
        return [app_label.capitalize()]
        