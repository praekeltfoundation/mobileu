from import_export import resources
from communication.models import SmsQueue, Sms


class SmsQueueResource(resources.ModelResource):

    class Meta:
        model = SmsQueue
        fields = (
            'message',
            'sent_date',
            'msisdn',
            'sent',
            'sent_date',
        )
        export_order = (
            'message',
            'sent_date',
            'msisdn',
            'sent',
            'sent_date',
        )


class SmsResource(resources.ModelResource):

    class Meta:
        model = Sms
        fields = (
            'uuid',
            'message',
            'date_sent',
            'msisdn',
            'responded',
            'respond_date',
            'response',
            'sent_date',
        )
        export_order = (
            'uuid',
            'message',
            'date_sent',
            'msisdn',
            'responded',
            'respond_date',
            'response',
            'sent_date',
        )
