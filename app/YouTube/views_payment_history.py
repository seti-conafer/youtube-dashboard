from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.shortcuts import render

from .models import Client, Asset, AssetGroup, AssetRevenueView, PromotionVideo


@login_required
def payment_history(request, client_id, year_month):
  client = Client.objects.get(id=client_id)
  asset_groups = AssetGroup.objects.filter(client=client)
  assets = Asset.objects.filter(asset_group__in=asset_groups)
  ch_groups = asset_groups.filter(asset_type='ch')
  at_groups = asset_groups.filter(asset_type='at')
  sr_groups = asset_groups.filter(asset_type='sr')
  # print(sr_groups)

  mc_revenues = {}
  ch_revenues = {}
  for ag in ch_groups:
    rev = AssetRevenueView.objects.filter(asset__in=Asset.objects.filter(asset_group=ag), year_month=year_month, manual_claimed=False, promotion=False)
    if len(rev) > 0:
      ch_revenues[ag.group_name] = {
        'total': rev.aggregate(Sum('partner_revenue'))['partner_revenue__sum'],
        'split': rev.aggregate(Sum('partner_revenue'))['partner_revenue__sum'] * float(client.channel_split)
      }
    mc_rev = AssetRevenueView.objects.filter(asset__in=Asset.objects.filter(asset_group=ag), year_month=year_month, manual_claimed=True, promotion=False)
    if len(mc_rev) > 0:
      mc_revenues[ag.group_name] = {
        'total': mc_rev.aggregate(Sum('partner_revenue'))['partner_revenue__sum'],
        'split': mc_rev.aggregate(Sum('partner_revenue'))['partner_revenue__sum'] * float(client.mc_split)
      }

  at_revenues = {}
  for ag in at_groups:
    rev = AssetRevenueView.objects.filter(asset__in=Asset.objects.filter(asset_group=ag), year_month=year_month, manual_claimed=False, promotion=False)
    if len(rev) > 0:
      at_revenues[ag.group_name] = {
        'total': rev.aggregate(Sum('partner_revenue'))['partner_revenue__sum'],
        'split': rev.aggregate(Sum('partner_revenue'))['partner_revenue__sum'] * float(client.at_split)
      }
    mc_rev = AssetRevenueView.objects.filter(asset__in=Asset.objects.filter(asset_group=ag), year_month=year_month, manual_claimed=True, promotion=False)
    if len(mc_rev) > 0:
      mc_revenues[ag.group_name] = {
        'total': mc_rev.aggregate(Sum('partner_revenue'))['partner_revenue__sum'],
        'split': mc_rev.aggregate(Sum('partner_revenue'))['partner_revenue__sum'] * float(client.mc_split)
      }

  sr_revenues = {}
  promo_revenues = {}
  for ag in sr_groups:
    sr_assets = Asset.objects.filter(asset_group=ag)
    rev = AssetRevenueView.objects.filter(asset__in=sr_assets, year_month=year_month, manual_claimed=False, promotion=False)
    if len(rev) > 0:
      sr_revenues[ag.group_name] = {
        'total': rev.aggregate(Sum('partner_revenue'))['partner_revenue__sum'],
        'split': rev.aggregate(Sum('partner_revenue'))['partner_revenue__sum'] * float(client.sr_split)
      }
    mc_rev = AssetRevenueView.objects.filter(asset__in=Asset.objects.filter(asset_group=ag), year_month=year_month, manual_claimed=True, promotion=False)
    if len(mc_rev) > 0:
      mc_revenues[ag.group_name] = {
        'total': mc_rev.aggregate(Sum('partner_revenue'))['partner_revenue__sum'],
        'split': mc_rev.aggregate(Sum('partner_revenue'))['partner_revenue__sum'] * float(client.mc_split)
      }
    promotion_video = PromotionVideo.objects.filter(included_asset__in=sr_assets).distinct()
    for vid in promotion_video:
      split = sr_assets.filter(asset_id__in=vid.included_asset.all()).count() / vid.included_asset.all().count()
      # print(vid.asset.asset_title, AssetRevenueView.objects.filter(asset_id=vid.asset_id).aggregate(Sum('partner_revenue'))['partner_revenue__sum'])
      promo_rev_objects = AssetRevenueView.objects.filter(asset_id=vid.asset_id, year_month=year_month)
      if len(promo_rev_objects) > 0:
        promo_total_sum = promo_rev_objects.aggregate(Sum('partner_revenue'))['partner_revenue__sum'] * split
      else:
        promo_total_sum = 0
      promo_revenues[Asset.objects.get(asset_id=vid.asset_id).asset_title] = {
        'total': promo_total_sum,
        'split': promo_total_sum * 0.4
      }

  promo_revenues = dict(sorted(promo_revenues.items(), key=lambda x: x[1]['total'], reverse=True))


  total_revenue = {}
  split_revenue = {}
  total_revenue['ch'] = 0
  split_revenue['ch'] = 0
  total_revenue['at'] = 0
  split_revenue['at'] = 0
  total_revenue['sr'] = 0
  split_revenue['sr'] = 0
  total_revenue['mc'] = 0
  split_revenue['mc'] = 0
  total_revenue['pm'] = 0
  split_revenue['pm'] = 0
  for revenue in ch_revenues:
    total_revenue['ch'] += ch_revenues[revenue]['total']
    split_revenue['ch'] += ch_revenues[revenue]['split']
  for revenue in at_revenues:
    total_revenue['at'] += at_revenues[revenue]['total']
    split_revenue['at'] += at_revenues[revenue]['split']
  for revenue in sr_revenues:
    total_revenue['sr'] += sr_revenues[revenue]['total']
    split_revenue['sr'] += sr_revenues[revenue]['split']
  for revenue in mc_revenues:
    total_revenue['mc'] += mc_revenues[revenue]['total']
    split_revenue['mc'] += mc_revenues[revenue]['split']
  for revenue in promo_revenues:
    total_revenue['pm'] += promo_revenues[revenue]['total']
    split_revenue['pm'] += promo_revenues[revenue]['split']

  total_sum = 0
  for key, value in total_revenue.items():
    total_sum += value

  split_sum = 0
  for key, value in split_revenue.items():
    split_sum += value

  context = {
    'client': client,
    'year_month': year_month,
    'ch_revenues': ch_revenues,
    'at_revenues': at_revenues,
    'sr_revenues': sr_revenues,
    'mc_revenues': mc_revenues,
    'promo_revenues': promo_revenues,
    'total_revenue': total_revenue,
    'split_revenue': split_revenue,
    'total_sum': total_sum,
    'split_sum': split_sum,
  }
  return render(request, 'revenue_detail.html', context)
