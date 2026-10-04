import { NextResponse } from 'next/server';
import type { KSamsokResult } from '@/lib/ksamsok';

type KSamsokText = string | { '@value'?: string };
const textValue = (d: KSamsokText) => (typeof d === 'string' ? d : d['@value'] || '');

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const query = searchParams.get('q');

  if (!query) {
    return NextResponse.json({ error: 'Missing query parameter' }, { status: 400 });
  }

  try {
    // Search for images matching the query
    const apiUrl = `https://kulturarvsdata.se/ksamsok/api?method=search&query=text="${encodeURIComponent(query)}" AND thumbnailExists=j&hitsPerPage=20`;
    
    const response = await fetch(apiUrl, {
      headers: {
        'Accept': 'application/json'
      }
    });

    if (!response.ok) {
      throw new Error(`K-Samsök API error: ${response.statusText}`);
    }

    const data = await response.json();
    const results: KSamsokResult[] = [];

    const records = data?.result?.records || [];
    for (const record of records) {
      const graph = record?.record?.['@graph'] || [];
      
      let imageUrl = '';
      let thumbUrl = '';
      let desc = '';
      
      for (const node of graph) {
        // Current K-samsök format: images are ksam:Media nodes with a ksam:link
        if (node['@type'] === 'ksam:Media' && !imageUrl) {
          const mediaType = textValue(node['ksam:mediaType'] || '');
          const link = textValue(node['ksam:link'] || '');
          if (link && (!mediaType || mediaType.startsWith('image/'))) {
            imageUrl = link;
          }
        }
        if (node['@type'] === 'ksam:ItemName' && node['ksam:name'] && !desc) {
          desc = textValue(node['ksam:name']);
        }

        // Older format
        if (node.highresSource) {
          imageUrl = node.highresSource;
        } else if (node.lowresSource && !imageUrl) {
          imageUrl = node.lowresSource;
        }
        
        if (node.thumbnailSource) {
          thumbUrl = node.thumbnailSource;
        }
        
        if (node['ksam:desc']) {
          if (Array.isArray(node['ksam:desc'])) {
             desc = node['ksam:desc'].map((d: KSamsokText) => textValue(d)).join(', ');
          } else {
             desc = textValue(node['ksam:desc']);
          }
        }
      }

      if (imageUrl) {
        results.push({
          url: imageUrl,
          thumbnail: thumbUrl || imageUrl,
          description: desc || 'Bild från K-Samsök'
        });
      }
    }

    return NextResponse.json({ results });
  } catch (error) {
    console.error('K-Samsök fetch error:', error);
    return NextResponse.json({ error: 'Failed to fetch data from K-Samsök' }, { status: 500 });
  }
}
