from google.appengine.ext import ndb

def sanitize_model_property(p):
    if isinstance(p, ndb.Key):
        return p.urlsafe()
    return p

class FancyModel(ndb.Model):
    def to_dict(self, *args, **kwargs):
        dict_result = super(FancyModel,self).to_dict(*args, **kwargs)
        sanitized_result = {k: sanitize_model_property(v) for k, v in dict_result.items()}
        sanitized_result['key'] = self.key.urlsafe()
        return sanitized_result