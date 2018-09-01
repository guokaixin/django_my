

class ImageMixin(object):

    def thumb_url(self, quality=30):
        if getattr(self, 'image', None):
            return '%s?x-oss-process=image/quality,q_%s' % (self.image.url, quality)
        return ''

    def continent_map_thumb_url(self, quality=40):
        if getattr(self, 'continent_map', None):
            return '%s?x-oss-process=image/quality,q_%s' % (self.continent_map.url, quality)
        return ''

    def country_map_thumb_url(self, quality=40):
        if getattr(self, 'country_map', None):
            return '%s?x-oss-process=image/quality,q_%s' % (self.country_map.url, quality)
        return ''

    def city_map_thumb_url(self, quality=40):
        if getattr(self, 'city_map', None):
            return '%s?x-oss-process=image/quality,q_%s' % (self.city_map.url, quality)
        return ''

    def route_image_thumb_url(self, quality=40):
        if getattr(self, 'route_image', None):
            return '%s?x-oss-process=image/quality,q_%s' % (self.route_image.url, quality)
        return ''

    def banner_thumb_url(self, quality=40):
        if getattr(self, 'link_image', None):
            return '%s?x-oss-process=image/quality,q_%s' % (self.link_image.url, quality)
        return ''
